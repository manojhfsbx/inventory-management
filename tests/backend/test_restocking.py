"""
Tests for restocking API endpoints.
"""
import pytest
from datetime import datetime


class TestRestockRecommendationsEndpoint:
    """Test suite for the restock recommendations endpoint."""

    def test_get_recommendations_basic_structure(self, client):
        """Test that the recommendations response has the expected top-level shape."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "total_recommended_cost" in data
        assert "remaining_budget" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert data["budget"] == 5000

    def test_recommendation_item_structure(self, client):
        """Test that each recommendation has all required fields."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()
        assert len(data["recommendations"]) > 0

        required_fields = [
            "sku", "name", "current_demand", "forecasted_demand", "trend",
            "quantity_on_hand", "reorder_point", "unit_cost", "urgency",
            "growth", "score", "suggested_qty", "recommended_qty", "cost", "included",
        ]
        for item in data["recommendations"]:
            for field in required_fields:
                assert field in item, f"Missing field {field} in recommendation"
            assert item["included"] is True

    def test_recommendations_sorted_by_score_descending(self, client):
        """Test that recommendations are returned in priority-score order."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()
        scores = [item["score"] for item in data["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_recommendations_cost_never_exceeds_budget(self, client):
        """Test that the total recommended cost never exceeds the given budget."""
        budget = 500
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        data = response.json()
        assert data["total_recommended_cost"] <= budget + 0.01

    def test_zero_budget_returns_no_recommendations(self, client):
        """Test that a zero budget recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["recommendations"] == []
        assert data["total_recommended_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget is rejected with a 400."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_large_budget_covers_every_joinable_item(self, client):
        """Test that a very large budget includes every demand-forecast item that
        joins to an inventory SKU and has positive forecasted growth."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        data = response.json()

        inventory_skus = {item["sku"] for item in client.get("/api/inventory").json()}
        demand_items = client.get("/api/demand").json()
        joinable = [
            d for d in demand_items
            if d["item_sku"] in inventory_skus and d["forecasted_demand"] > d["current_demand"]
        ]

        assert len(data["recommendations"]) == len(joinable)
        returned_skus = {item["sku"] for item in data["recommendations"]}
        assert returned_skus == {d["item_sku"] for d in joinable}

    def test_declining_demand_item_never_recommended(self, client):
        """Test that an item whose forecasted demand is below current demand
        (suggested_qty would be 0) never appears, at any budget."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        data = response.json()
        skus = {item["sku"] for item in data["recommendations"]}
        assert "MTR-304" not in skus

    def test_recommended_qty_never_exceeds_suggested_qty(self, client):
        """Test that budget trimming never recommends more than the suggested quantity."""
        response = client.get("/api/restocking/recommendations?budget=300")
        data = response.json()
        assert len(data["recommendations"]) > 0
        for item in data["recommendations"]:
            assert item["recommended_qty"] <= item["suggested_qty"]

    def test_increasing_budget_never_removes_items(self, client):
        """Test that recommendations for a larger budget are a superset of a smaller one
        (monotonic inclusion, since items are filled in stable score order)."""
        small = client.get("/api/restocking/recommendations?budget=50").json()
        large = client.get("/api/restocking/recommendations?budget=100000").json()

        small_skus = {item["sku"] for item in small["recommendations"]}
        large_skus = {item["sku"] for item in large["recommendations"]}
        assert small_skus.issubset(large_skus)


class TestRestockOrderCreationEndpoint:
    """Test suite for submitting a restocking order."""

    def test_create_restock_order_success(self, client):
        """Test that a valid restock order is created with the expected fields."""
        payload = {
            "items": [
                {"sku": "PSU-501", "name": "5V 10A Switching Power Supply",
                 "quantity": 10, "unit_price": 18.99}
            ],
            "budget": 500,
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["source"] == "restocking"
        assert data["status"] == "Processing"
        assert data["customer"] == "Internal Restocking"
        assert abs(data["total_value"] - 189.9) < 0.01
        assert data["items"] == payload["items"]

    def test_create_restock_order_appears_in_orders_list(self, client):
        """Test that a submitted restock order shows up in GET /api/orders."""
        payload = {
            "items": [{"sku": "PSU-501", "name": "5V 10A Switching Power Supply",
                       "quantity": 5, "unit_price": 18.99}]
        }
        create_response = client.post("/api/restocking/orders", json=payload)
        order_number = create_response.json()["order_number"]

        orders_response = client.get("/api/orders")
        all_orders = orders_response.json()
        assert any(o["order_number"] == order_number for o in all_orders)
        matching = next(o for o in all_orders if o["order_number"] == order_number)
        assert matching["source"] == "restocking"

    def test_create_restock_order_lead_time_is_14_days(self, client):
        """Test that expected_delivery is exactly 14 days after order_date."""
        payload = {
            "items": [{"sku": "PSU-501", "name": "5V 10A Switching Power Supply",
                       "quantity": 1, "unit_price": 18.99}]
        }
        response = client.post("/api/restocking/orders", json=payload)
        data = response.json()

        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        assert (expected_delivery - order_date).days == 14

    def test_create_restock_order_empty_items_rejected(self, client):
        """Test that submitting an order with no items is rejected with a 400."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_restock_order_survives_category_filter(self, client):
        """Test that a restocking order (which has no single category) doesn't
        crash and isn't silently dropped when a category filter is applied."""
        payload = {
            "items": [{"sku": "PSU-501", "name": "5V 10A Switching Power Supply",
                       "quantity": 5, "unit_price": 18.99}]
        }
        create_response = client.post("/api/restocking/orders", json=payload)
        order_number = create_response.json()["order_number"]

        response = client.get("/api/orders?category=Power Supplies")
        assert response.status_code == 200
        order_numbers = [o["order_number"] for o in response.json()]
        assert order_number in order_numbers

    def test_restock_order_survives_warehouse_filter(self, client):
        """Test that a restocking order (which has no single warehouse) doesn't
        get silently dropped when a warehouse filter is applied."""
        payload = {
            "items": [{"sku": "PSU-501", "name": "5V 10A Switching Power Supply",
                       "quantity": 5, "unit_price": 18.99}]
        }
        create_response = client.post("/api/restocking/orders", json=payload)
        order_number = create_response.json()["order_number"]

        response = client.get("/api/orders?warehouse=Tokyo")
        assert response.status_code == 200
        order_numbers = [o["order_number"] for o in response.json()]
        assert order_number in order_numbers

    def test_create_restock_order_multiple_items(self, client):
        """Test that an order with multiple items sums total_value correctly."""
        payload = {
            "items": [
                {"sku": "PSU-501", "name": "5V 10A Switching Power Supply",
                 "quantity": 10, "unit_price": 18.99},
                {"sku": "WDG-001", "name": "Industrial Widget Type A",
                 "quantity": 50, "unit_price": 15.0},
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 2
        assert abs(data["total_value"] - (10 * 18.99 + 50 * 15.0)) < 0.01
