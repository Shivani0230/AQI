
def health_recommendation(aqi: int, pm25: float = None, humidity: float = None) -> str:
    if aqi <= 50:
        return "Great air today — enjoy outdoor exercise."
    if aqi <= 100:
        return "Air is acceptable — sensitive groups should be mindful."
    if aqi <= 150:
        return "Unhealthy for sensitive groups — reduce prolonged outdoor exertion."
    if aqi <= 200:
        return "Unhealthy — limit outdoor activity; consider a mask if sensitive."
    if aqi <= 300:
        return "Very Unhealthy — avoid outdoor activity; use N95 if you must go out."
    return "Hazardous — stay indoors with air filtration; avoid all outdoor exertion."
