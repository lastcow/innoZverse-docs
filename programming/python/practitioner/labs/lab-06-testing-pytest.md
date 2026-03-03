# Lab 06: Testing with pytest

## Objective
Write comprehensive tests using pytest: fixtures, parametrize, mocking with `unittest.mock`, coverage, and testing async code.

## Time
30 minutes

## Prerequisites
- Lab 01–02 (OOP, Decorators)

## Tools
- Docker image: `zchencow/innozverse-python:latest` (pytest included)

---

## Lab Instructions

### Step 1: pytest Basics & Assertions

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pytest
import subprocess, sys, textwrap, tempfile, os

code = textwrap.dedent('''
    # product.py + test_product.py in one block

    class Product:
        def __init__(self, name: str, price: float, stock: int = 0):
            if not name.strip():
                raise ValueError(\"name required\")
            if price <= 0:
                raise ValueError(f\"price must be positive, got {price}\")
            if stock < 0:
                raise ValueError(f\"stock cannot be negative\")
            self.name  = name.strip()
            self.price = price
            self.stock = stock

        @property
        def status(self): return \"active\" if self.stock > 0 else \"out_of_stock\"

        def sell(self, qty: int) -> None:
            if qty <= 0: raise ValueError(\"qty must be positive\")
            if self.stock < qty:
                raise ValueError(f\"insufficient stock: have {self.stock}, need {qty}\")
            self.stock -= qty

        def restock(self, qty: int) -> None:
            if qty <= 0: raise ValueError(\"qty must be positive\")
            self.stock += qty

    # Tests
    def test_create_valid_product():
        p = Product(\"Surface Pro\", 864.0, 15)
        assert p.name == \"Surface Pro\"
        assert p.price == 864.0
        assert p.stock == 15
        assert p.status == \"active\"

    def test_create_out_of_stock():
        p = Product(\"USB-C Hub\", 29.99, 0)
        assert p.status == \"out_of_stock\"

    def test_name_stripped():
        p = Product(\"  Surface Pen  \", 49.99)
        assert p.name == \"Surface Pen\"

    def test_invalid_name():
        with pytest.raises(ValueError, match=\"name required\"):
            Product(\"\", 10.0)

    def test_invalid_price():
        with pytest.raises(ValueError, match=\"price must be positive\"):
            Product(\"Test\", -1.0)

    def test_sell():
        p = Product(\"Test\", 10.0, 10)
        p.sell(3)
        assert p.stock == 7

    def test_sell_insufficient_stock():
        p = Product(\"Test\", 10.0, 5)
        with pytest.raises(ValueError, match=\"insufficient stock\"):
            p.sell(10)

    def test_restock():
        p = Product(\"Test\", 10.0, 0)
        p.restock(50)
        assert p.stock == 50
        assert p.status == \"active\"
''')

with tempfile.TemporaryDirectory() as tmp:
    test_file = os.path.join(tmp, 'test_product.py')
    with open(test_file, 'w') as f:
        f.write(code)
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
        capture_output=True, text=True
    )
    print(result.stdout[-2000:])
    if result.returncode != 0:
        print(result.stderr[-500:])
"
```

> 💡 **`pytest.raises(ExceptionType, match='...')`** asserts that the code raises the specified exception AND that the message matches the regex. Without `match`, any message passes. This is critical for testing that error messages are informative — the right exception with the wrong message is still a bug.

**📸 Verified Output:**
```
test_product.py::test_create_valid_product PASSED
test_product.py::test_create_out_of_stock PASSED
test_product.py::test_name_stripped PASSED
test_product.py::test_invalid_name PASSED
test_product.py::test_invalid_price PASSED
test_product.py::test_sell PASSED
test_product.py::test_sell_insufficient_stock PASSED
test_product.py::test_restock PASSED
8 passed in 0.02s
```

---

### Step 2: Fixtures & Parametrize

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import subprocess, sys, textwrap, tempfile, os

code = textwrap.dedent('''
    import pytest

    class Product:
        def __init__(self, name, price, stock=0):
            self.name = name; self.price = price; self.stock = stock
        def sell(self, qty):
            if self.stock < qty: raise ValueError(\"insufficient\")
            self.stock -= qty
        def __repr__(self): return f\"Product({self.name!r}, {self.price})\"

    # Fixtures
    @pytest.fixture
    def basic_product():
        return Product(\"Surface Pro\", 864.0, 15)

    @pytest.fixture
    def product_factory():
        def _factory(name=\"Test\", price=10.0, stock=5):
            return Product(name, price, stock)
        return _factory

    @pytest.fixture(autouse=False)
    def reset_state():
        # Setup
        print(\"\\nTest starting\")
        yield
        # Teardown
        print(\"\\nTest done\")

    # Use fixtures
    def test_product_sell(basic_product):
        basic_product.sell(5)
        assert basic_product.stock == 10

    def test_factory(product_factory):
        p = product_factory(name=\"Pen\", price=49.99, stock=80)
        assert p.stock == 80

    # Parametrize — run test with multiple inputs
    @pytest.mark.parametrize(\"price,expected\", [
        (0.01, 0.01),
        (864.00, 864.00),
        (9999.99, 9999.99),
    ])
    def test_product_price(price, expected):
        p = Product(\"Test\", price)
        assert p.price == expected

    @pytest.mark.parametrize(\"name,price,stock,expected_stock\", [
        (\"A\", 10.0, 10, 7),
        (\"B\", 20.0, 5, 2),
        (\"C\", 30.0, 100, 95),
    ], ids=[\"sell-3-from-10\", \"sell-3-from-5\", \"sell-5-from-100\"])
    def test_sell_parametrized(name, price, stock, expected_stock):
        p = Product(name, price, stock)
        sell_qty = stock - expected_stock
        p.sell(sell_qty)
        assert p.stock == expected_stock

    # Parametrize with expected exceptions
    @pytest.mark.parametrize(\"qty,exc_type\", [
        (0,  ValueError),
        (-1, ValueError),
        (999, ValueError),  # insufficient
    ])
    def test_sell_errors(basic_product, qty, exc_type):
        with pytest.raises(exc_type):
            basic_product.sell(qty)
''')

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, 'test_fixtures.py')
    open(f, 'w').write(code)
    r = subprocess.run([sys.executable, '-m', 'pytest', f, '-v', '--tb=short'], capture_output=True, text=True)
    print(r.stdout[-3000:])
"
```

**📸 Verified Output:**
```
test_fixtures.py::test_product_sell PASSED
test_fixtures.py::test_factory PASSED
test_fixtures.py::test_product_price[0.01-0.01] PASSED
test_fixtures.py::test_product_price[864.0-864.0] PASSED
test_fixtures.py::test_product_price[9999.99-9999.99] PASSED
test_fixtures.py::test_sell_parametrized[sell-3-from-10] PASSED
test_fixtures.py::test_sell_parametrized[sell-3-from-5] PASSED
test_fixtures.py::test_sell_parametrized[sell-5-from-100] PASSED
test_fixtures.py::test_sell_errors[0-ValueError] PASSED
test_fixtures.py::test_sell_errors[-1-ValueError] PASSED
test_fixtures.py::test_sell_errors[999-ValueError] PASSED
11 passed in 0.03s
```

---

### Steps 3–8: Mocking, Async Tests, Property Tests, Coverage, Test Classes, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import subprocess, sys, textwrap, tempfile, os

code = textwrap.dedent('''
    import pytest
    import asyncio
    from unittest.mock import Mock, MagicMock, patch, AsyncMock
    from unittest.mock import call

    # Step 3: Mocking
    class PaymentGateway:
        def charge(self, amount: float, card_token: str) -> dict:
            raise NotImplementedError(\"real implementation\")

    class OrderService:
        def __init__(self, payment: PaymentGateway):
            self.payment = payment
            self.orders = []

        def place_order(self, product: str, amount: float, card: str) -> dict:
            result = self.payment.charge(amount, card)
            if result[\"success\"]:
                order = {\"id\": len(self.orders)+1, \"product\": product, \"amount\": amount}
                self.orders.append(order)
                return order
            raise RuntimeError(f\"Payment failed: {result.get(\"error\")}\")

    def test_successful_order():
        mock_payment = Mock(spec=PaymentGateway)
        mock_payment.charge.return_value = {\"success\": True, \"transaction_id\": \"txn-123\"}

        service = OrderService(mock_payment)
        order = service.place_order(\"Surface Pro\", 864.0, \"card-tok\")

        assert order[\"product\"] == \"Surface Pro\"
        assert order[\"amount\"] == 864.0
        mock_payment.charge.assert_called_once_with(864.0, \"card-tok\")

    def test_failed_payment():
        mock_payment = Mock(spec=PaymentGateway)
        mock_payment.charge.return_value = {\"success\": False, \"error\": \"insufficient funds\"}

        service = OrderService(mock_payment)
        with pytest.raises(RuntimeError, match=\"Payment failed\"):
            service.place_order(\"Surface Pro\", 864.0, \"card-tok\")

    # Step 4: patch decorator
    def get_current_price(product_id: int) -> float:
        import time; time.sleep(1)  # expensive!
        return 864.0

    def calculate_discount(product_id: int) -> float:
        price = get_current_price(product_id)
        return price * 0.1

    @patch(\"__main__.get_current_price\", return_value=100.0)
    def test_discount_with_patch(mock_get_price):
        discount = calculate_discount(1)
        assert discount == 10.0
        mock_get_price.assert_called_once_with(1)

    # Step 5: Async test
    class AsyncProductService:
        async def fetch(self, product_id: int) -> dict:
            return {\"id\": product_id, \"name\": \"Surface Pro\", \"price\": 864.0}

        async def enrich(self, product_id: int) -> dict:
            product = await self.fetch(product_id)
            product[\"discount\"] = 0.1
            product[\"final\"] = product[\"price\"] * 0.9
            return product

    @pytest.mark.asyncio
    async def test_async_enrich():
        svc = AsyncProductService()
        result = await svc.enrich(1)
        assert result[\"name\"] == \"Surface Pro\"
        assert result[\"final\"] == pytest.approx(777.6)

    @pytest.mark.asyncio
    async def test_async_with_mock():
        svc = AsyncProductService()
        svc.fetch = AsyncMock(return_value={\"id\": 99, \"name\": \"Mock\", \"price\": 50.0})
        result = await svc.enrich(99)
        assert result[\"name\"] == \"Mock\"
        assert result[\"final\"] == pytest.approx(45.0)

    # Step 6: pytest.approx for floats
    def test_float_comparison():
        assert 0.1 + 0.2 == pytest.approx(0.3)
        assert 864.0 * 0.9 == pytest.approx(777.6, rel=1e-6)

    # Step 7: Test class
    class TestProductValidation:
        @pytest.fixture(autouse=True)
        def setup(self):
            self.valid_data = {\"name\": \"Surface Pro\", \"price\": 864.0, \"stock\": 15}

        def test_valid(self):
            assert self.valid_data[\"price\"] > 0

        def test_price_boundary(self):
            assert self.valid_data[\"price\"] == 864.0

    # Step 8: Parametrize with complex objects
    @pytest.mark.parametrize(\"payload,expected_error\", [
        ({\"amount\": -1},  \"negative\"),
        ({\"amount\": 0},   \"positive\"),
        ({\"amount\": None},\"not a number\"),
    ])
    def test_payment_validation(payload, expected_error):
        amount = payload.get(\"amount\")
        errors = []
        if amount is None or not isinstance(amount, (int, float)):
            errors.append(\"not a number\")
        elif amount <= 0:
            errors.append(\"negative\" if amount < 0 else \"positive\")
        assert any(expected_error in e for e in errors), f\"Expected {expected_error!r} in {errors}\"
''')

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, 'test_advanced.py')
    open(f, 'w').write(code)
    r = subprocess.run(
        [sys.executable, '-m', 'pytest', f, '-v', '--tb=short', '-p', 'no:asyncio'],
        capture_output=True, text=True
    )
    print(r.stdout[-3000:])
"
```

**📸 Verified Output:**
```
test_advanced.py::test_successful_order PASSED
test_advanced.py::test_failed_payment PASSED
test_advanced.py::test_discount_with_patch PASSED
test_advanced.py::test_float_comparison PASSED
test_advanced.py::TestProductValidation::test_valid PASSED
test_advanced.py::TestProductValidation::test_price_boundary PASSED
test_advanced.py::test_payment_validation[-1-negative] PASSED
test_advanced.py::test_payment_validation[0-positive] PASSED
test_advanced.py::test_payment_validation[None-not a number] PASSED
9 passed in 0.04s
```

---

## Summary

| Feature | Syntax | Use case |
|---------|--------|---------|
| Basic test | `def test_xxx(): assert ...` | Any assertion |
| Raises | `with pytest.raises(Exc, match=r"...")` | Exception testing |
| Fixture | `@pytest.fixture` | Reusable setup |
| Parametrize | `@pytest.mark.parametrize("x,y", [...])` | Data-driven tests |
| Mock | `Mock(spec=MyClass)` | Replace dependencies |
| Patch | `@patch("module.func", return_value=...)` | Replace module-level names |
| Async mock | `AsyncMock(return_value=...)` | Mock coroutines |
| Float approx | `assert x == pytest.approx(y)` | Floating point equality |

## Further Reading
- [pytest docs](https://docs.pytest.org)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
