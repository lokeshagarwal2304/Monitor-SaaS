import time
import httpx
from fastapi import APIRouter, Query, HTTPException, status

router = APIRouter(prefix="/pagespeed", tags=["PageSpeed"])

@router.get("/")
async def get_page_speed(url: str = Query(..., description="URL to check page speed for")):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        start_time = time.time()
        # Use simple GET request to measure response time
        async with httpx.AsyncClient(headers={"User-Agent": "MoniFy-Ping/1.0"}, follow_redirects=True) as client:
            response = await client.get(url, timeout=15)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000
        
        return {
            "url": url,
            "status_code": response.status_code,
            "response_time_ms": round(response_time_ms, 2),
            "message": f"Server responded in {round(response_time_ms, 2)}ms."
        }
        
    except httpx.ConnectTimeout:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Connection timeout after 15 seconds.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error checking speed: {e}")