# Mangrove Visualization API Documentation

## Overview
API untuk sistem visualisasi data mangrove dengan dukungan operasi CRUD lengkap untuk layer raster dan data vektor mangrove.

## Authentication
Semua endpoint memerlukan authentication kecuali GET requests untuk data publik.

## Endpoints

### Health Check
```
GET /api/health/
```
**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2026-03-30T08:50:29Z",
    "service": "Mangrove Visualization API"
}
```

### Mangrove Sites (Vector Data)

#### List Mangrove Sites
```
GET /api/mangroves/
```
**Query Parameters:**
- `search`: Search by name, species, or source
- `in_bbox`: Filter by bounding box (minx,miny,maxx,maxy)

**Response:**
```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [123.456, -5.678]
            },
            "properties": {
                "id": 1,
                "name": "Mangrove Site A",
                "species": "Avicennia marina",
                "canopy_cover": 85.5,
                "source": "Survey 2026",
                "created_at": "2026-03-30T08:00:00Z"
            }
        }
    ]
}
```

#### Create Mangrove Site
```
POST /api/mangroves/
```
**Request Body:**
```json
{
    "name": "New Mangrove Site",
    "species": "Rhizophora apiculata",
    "canopy_cover": 90.0,
    "source": "Field Survey",
    "geometry": {
        "type": "Point",
        "coordinates": [123.456, -5.678]
    }
}
```

#### Update Mangrove Site
```
PUT /api/mangroves/{id}/
PATCH /api/mangroves/{id}/
```

#### Delete Mangrove Site
```
DELETE /api/mangroves/{id}/
```
**Response:**
```json
{
    "message": "Mangrove site 'Site Name' deleted successfully"
}
```

### Raster Layers

#### List Raster Layers
```
GET /api/rasters/
```
**Response:**
```json
[
    {
        "id": 1,
        "name": "Mangrove Classification 2026",
        "url": "/media/rasters/mangrove_2026.tif",
        "epsg": 4326,
        "width": 1024,
        "height": 768,
        "minx": 123.0,
        "miny": -6.0,
        "maxx": 124.0,
        "maxy": -5.0,
        "created_at": "2026-03-30T08:00:00Z"
    }
]
```

#### Upload Raster Layer
```
POST /api/rasters/
```
**Request:** Multipart form data
- `name`: Layer name
- `file`: GeoTIFF file

#### Update Raster Layer
```
PUT /api/rasters/{id}/
PATCH /api/rasters/{id}/
```

#### Delete Raster Layer
```
DELETE /api/rasters/{id}/
```
**Response:**
```json
{
    "message": "Raster layer 'Layer Name' and associated files deleted successfully"
}
```
**Note:** Delete operation will also remove:
- Original GeoTIFF file
- Reprojected file (if exists)
- Generated tiles directory

## Error Responses

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

## File Cleanup on Delete

When deleting raster layers, the system automatically cleans up associated files:
- Original uploaded GeoTIFF file
- Reprojected EPSG:4326 version
- Generated XYZ tiles directory
- Database metadata record

## Admin Interface

### Django Admin Access
- URL: `/admin/`
- Features:
  - Full CRUD operations for both models
  - File cleanup on raster deletion
  - Bulk delete with file cleanup
  - Search and filtering capabilities

## Usage Examples

### JavaScript (Frontend Integration)
```javascript
// Get mangrove sites within map bounds
const bounds = map.getBounds();
const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;

fetch(`/api/mangroves/?in_bbox=${bbox}`)
    .then(response => response.json())
    .then(data => {
        // Add to map
        L.geoJSON(data).addTo(map);
    });

// Delete raster layer
fetch(`/api/rasters/${layerId}/`, {
    method: 'DELETE',
    headers: {
        'Authorization': 'Bearer ' + token
    }
})
.then(response => {
    if (response.ok) {
        // Remove from UI
        map.removeLayer(rasterLayer);
    }
});
```

### Python (Backend Integration)
```python
import requests

# Health check
response = requests.get('http://10.6.4.70:3031/api/health/')
print(response.json())

# Delete raster layer
headers = {'Authorization': f'Bearer {token}'}
response = requests.delete(f'http://10.6.4.70:3031/api/rasters/{layer_id}/', headers=headers)
print(response.json())
```

## Security Notes

- All write operations (POST, PUT, DELETE) require authentication
- File uploads are validated for GeoTIFF format
- Automatic cleanup prevents orphaned files
- CSRF protection enabled for web interface
- CORS configured for cross-origin requests

## Performance Considerations

- Raster processing is asynchronous
- Large file uploads may take time
- Tile generation runs in background
- Database queries optimized with indexes
- File cleanup runs synchronously on delete