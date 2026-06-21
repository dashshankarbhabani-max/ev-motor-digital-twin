# Render deployment

This API runs the saved machine-learning model locally on the Render server. It
does not call Gemini or any other AI service.

## Deploy

1. Push this project to a private GitHub repository. Do not commit `.env`.
2. In Render, create a Blueprint and select the repository. Render reads
   `render.yaml` automatically.
3. When Render asks for `APP_API_KEY`, paste the value from your local `.env`.
4. Deploy the service and open `https://YOUR-SERVICE.onrender.com/health`.

## Call the API

```bash
curl -X POST "https://YOUR-SERVICE.onrender.com/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_APP_API_KEY" \
  -d '{
    "voltage_v": 400,
    "current_a": 100,
    "speed_rpm": 6000,
    "torque_nm": 200,
    "flux_estimate": 0.8
  }'
```

Generate a replacement key at any time with:

```bash
python generate_api_key.py
```

Update `APP_API_KEY` in Render whenever the key is rotated.
