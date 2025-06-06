import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app  # Import your FastAPI app

@pytest.mark.asyncio
async def test_login_for_access_token():
    form_data = {
        "username": "admin",
        "password": "secret",
    }


    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/token", data=form_data)

    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_create_qr_code_unauthorized():
    # Attempt to create a QR code without authentication
    qr_request = {
        "url": "https://example.com",
        "fill_color": "red",
        "back_color": "white",
        "size": 10,
    }

    # ✅ Use ASGITransport to simulate FastAPI app in memory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/qr-codes/", json=qr_request)

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_and_delete_qr_code():
    form_data = {
        "username": "admin",
        "password": "secret",
    }

    # ✅ Correctly use ASGITransport to test FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login and get the access token
        token_response = await ac.post("/token", data=form_data)
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create a QR code
        qr_request = {
            "url": "https://example.com",
            "fill_color": "red",
            "back_color": "white",
            "size": 10,
        }
        create_response = await ac.post("/qr-codes/", json=qr_request, headers=headers)
        assert create_response.status_code in [200, 201, 409]

        # If QR code was created or already exists, attempt to delete it
        if create_response.status_code in [200, 201]:
            response_json = create_response.json()
            # Try direct access first
            qr_code_url = response_json.get("qr_code_url")

        # Fallback: extract from "links"
        if not qr_code_url:
            for link in response_json.get("links", []):
                if link.get("rel") == "view":
                    qr_code_url = link.get("href")
                    break

        assert qr_code_url, "QR code URL could not be extracted from response"
        qr_filename = qr_code_url.split("/")[-1]

        delete_response = await ac.delete(f"/qr-codes/{qr_filename}", headers=headers)
        assert delete_response.status_code == 204