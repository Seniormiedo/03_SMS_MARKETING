#!/usr/bin/env python3
"""
Test script to verify dashboard integration with backend
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class DashboardIntegrationTester:
    """Test dashboard integration with backend"""

    def __init__(self):
        self.backend_url = "http://localhost:8000/api/v1"
        self.dashboard_url = "http://localhost:3000"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_backend_endpoints(self) -> Dict[str, Any]:
        """Test all backend endpoints needed by dashboard"""
        results = {}

        endpoints_to_test = [
            ("/health", "Health check"),
            ("/dashboard/stats", "Enhanced stats for dashboard"),
            ("/dashboard/contacts?page=1&page_size=10", "Paginated contacts"),
            ("/dashboard/states", "Available states"),
            ("/dashboard/ladas", "Available LADAs"),
        ]

        for endpoint, description in endpoints_to_test:
            try:
                response = await self.client.get(f"{self.backend_url}{endpoint}")
                results[endpoint] = {
                    "status": "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})",
                    "description": description,
                    "response_time": response.elapsed.total_seconds(),
                    "data_sample": str(response.json())[:200] + "..." if response.status_code == 200 else None
                }
            except Exception as e:
                results[endpoint] = {
                    "status": f"❌ ERROR",
                    "description": description,
                    "error": str(e)
                }

        return results

    async def test_dashboard_connectivity(self) -> Dict[str, Any]:
        """Test dashboard connectivity"""
        try:
            response = await self.client.get(self.dashboard_url)
            return {
                "status": "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "❌ ERROR",
                "error": str(e)
            }

    async def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration"""
        try:
            # Simulate preflight request
            response = await self.client.options(
                f"{self.backend_url}/contacts/stats-enhanced",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )

            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }

            return {
                "status": "✅ PASS" if response.status_code in [200, 204] else f"❌ FAIL ({response.status_code})",
                "cors_headers": cors_headers
            }
        except Exception as e:
            return {
                "status": "❌ ERROR",
                "error": str(e)
            }

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🔄 Testing Dashboard Integration with Backend...")
        print("=" * 60)

        # Test backend endpoints
        print("\n📊 Testing Backend Endpoints:")
        backend_results = await self.test_backend_endpoints()
        for endpoint, result in backend_results.items():
            print(f"  {result['status']} {endpoint} - {result['description']}")
            if result.get('response_time'):
                print(f"    ⏱️  Response time: {result['response_time']:.3f}s")
            if result.get('error'):
                print(f"    ❌ Error: {result['error']}")

        # Test dashboard
        print("\n🖥️  Testing Dashboard:")
        dashboard_result = await self.test_dashboard_connectivity()
        print(f"  {dashboard_result['status']} Dashboard accessibility")
        if dashboard_result.get('response_time'):
            print(f"    ⏱️  Response time: {dashboard_result['response_time']:.3f}s")

        # Test CORS
        print("\n🔗 Testing CORS Configuration:")
        cors_result = await self.test_cors_configuration()
        print(f"  {cors_result['status']} CORS headers")
        if cors_result.get('cors_headers'):
            for header, value in cors_result['cors_headers'].items():
                if value:
                    print(f"    ✅ {header}: {value}")

        # Summary
        print("\n" + "=" * 60)
        backend_passed = sum(1 for r in backend_results.values() if "✅ PASS" in r['status'])
        backend_total = len(backend_results)

        print(f"📊 Backend Endpoints: {backend_passed}/{backend_total} passed")
        print(f"🖥️  Dashboard: {dashboard_result['status']}")
        print(f"🔗 CORS: {cors_result['status']}")

        if backend_passed == backend_total and "✅ PASS" in dashboard_result['status'] and "✅ PASS" in cors_result['status']:
            print("\n🎉 ¡INTEGRACIÓN EXITOSA! Dashboard ↔ Backend funcionando correctamente")
            return True
        else:
            print("\n⚠️  Hay problemas de integración que necesitan resolverse")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def main():
    """Main test function"""
    tester = DashboardIntegrationTester()

    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.close()

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
