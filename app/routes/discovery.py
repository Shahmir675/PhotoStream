from fastapi import APIRouter, Request
import httpx
import os
import logging

router = APIRouter(prefix="/api", tags=["Discovery"])
logger = logging.getLogger(__name__)

# Regional server mapping - update these after deployment
REGIONAL_SERVERS = {
    "us-west": os.getenv("SERVER_US_WEST", "https://photostream-api-us-west.onrender.com"),
    "us-east": os.getenv("SERVER_US_EAST", "https://photostream-api-us-east.onrender.com"),
    "eu-central": os.getenv("SERVER_EU", "https://photostream-api-eu.onrender.com"),
}


@router.get("/discover")
async def discover_server(request: Request):
    """
    Returns the best server for the client based on geographic location.

    Usage:
    1. Client calls this endpoint from ANY regional server
    2. Endpoint detects client's location via IP
    3. Returns the nearest server URL
    4. Client uses that URL for subsequent requests

    Example response:
    {
        "server": "https://photostream-api-eu.onrender.com",
        "region": "eu-central",
        "client_ip": "195.123.456.789",
        "detected_location": {
            "country": "DE",
            "continent": "EU",
            "city": "Frankfurt"
        }
    }
    """
    # Get client IP (handle proxy headers)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)

    # Handle multiple IPs in X-Forwarded-For
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    # Remove port if present
    if ":" in client_ip and not "::" in client_ip:  # Not IPv6
        client_ip = client_ip.split(":")[0]

    logger.info(f"Discovery request from IP: {client_ip}")

    # Skip geo-lookup for localhost/private IPs
    if client_ip in ["127.0.0.1", "localhost", "::1"] or client_ip.startswith("192.168.") or client_ip.startswith("10."):
        logger.info("Localhost detected, returning default region")
        return {
            "server": REGIONAL_SERVERS["us-west"],
            "region": "us-west",
            "client_ip": client_ip,
            "reason": "localhost_default"
        }

    try:
        # Use free IP geolocation service (ipapi.co allows 1000 requests/day for free)
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"https://ipapi.co/{client_ip}/json/")

            if response.status_code != 200:
                raise Exception(f"Geo API returned status {response.status_code}")

            geo_data = response.json()

        continent = geo_data.get("continent_code", "NA")
        country = geo_data.get("country_code", "US")
        longitude = geo_data.get("longitude", -100)

        logger.info(f"Detected location: {country}, {continent}, long: {longitude}")

        # Route based on location
        if continent == "EU":
            # Europe -> EU server
            region = "eu-central"
        elif continent == "AF":
            # Africa -> EU server (closest)
            region = "eu-central"
        elif country in ["US", "CA", "MX"]:
            # North America - split by longitude (Rocky Mountains roughly -105)
            if longitude < -105:
                region = "us-west"  # West coast
            else:
                region = "us-east"  # East coast
        elif continent == "SA":
            # South America -> US East (closer)
            region = "us-east"
        elif continent in ["AS", "OC"]:
            # Asia/Oceania -> US West (Pacific)
            region = "us-west"
        else:
            # Default fallback
            region = "us-east"

        logger.info(f"Routing to region: {region}")

        return {
            "server": REGIONAL_SERVERS[region],
            "region": region,
            "client_ip": client_ip,
            "detected_location": {
                "country": country,
                "continent": continent,
                "city": geo_data.get("city"),
                "region": geo_data.get("region"),
            }
        }

    except Exception as e:
        # Fallback to current server on error
        current_region = os.getenv("REGION_NAME", "us-west")
        logger.error(f"Discovery error: {str(e)}, falling back to {current_region}")

        return {
            "server": REGIONAL_SERVERS.get(current_region, REGIONAL_SERVERS["us-west"]),
            "region": current_region,
            "client_ip": client_ip,
            "error": str(e),
            "reason": "fallback_to_current_region"
        }


@router.get("/regions")
async def list_regions():
    """
    List all available regional servers and their health status.

    Useful for:
    - Monitoring regional server health
    - Client-side latency testing
    - Admin dashboards
    """
    regions = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for region_name, server_url in REGIONAL_SERVERS.items():
            try:
                # Test health endpoint
                response = await client.get(f"{server_url}/api/health")
                health = response.json()

                status = "healthy" if health.get("status") == "healthy" else "unhealthy"
                response_time = response.elapsed.total_seconds() * 1000  # Convert to ms

                regions.append({
                    "region": region_name,
                    "url": server_url,
                    "status": status,
                    "response_time_ms": round(response_time, 2),
                    "database": health.get("database"),
                    "cache": health.get("cache"),
                })

            except Exception as e:
                logger.error(f"Region {region_name} health check failed: {str(e)}")
                regions.append({
                    "region": region_name,
                    "url": server_url,
                    "status": "offline",
                    "response_time_ms": None,
                    "error": str(e)
                })

    return {
        "regions": regions,
        "total_regions": len(regions),
        "healthy_regions": len([r for r in regions if r["status"] == "healthy"])
    }


@router.get("/ping")
async def ping():
    """
    Ultra-fast ping endpoint for client-side latency testing.

    Clients can ping all regional servers and choose the fastest.
    """
    return {
        "pong": True,
        "region": os.getenv("REGION_NAME", "unknown"),
        "timestamp": __import__("time").time()
    }
