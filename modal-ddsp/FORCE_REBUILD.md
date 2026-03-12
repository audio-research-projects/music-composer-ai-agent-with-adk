# Force Modal Image Rebuild

If you're getting TensorFlow version errors, the old cached image is being used.

## Option 1: Deploy with force flag

```bash
modal deploy modal_app.py --force
```

## Option 2: Delete and recreate the app

```bash
# Stop the app
modal app stop ddsp-timbre-transfer

# Redeploy
modal deploy modal_app.py
```

## Option 3: Change image hash

Modify the image definition slightly (add a comment, change order, etc.) to force rebuild:

```python
# In modal_app.py, change:
.pip_install(
    "tensorflow==2.11.1",
    # Add a comment or change order to invalidate cache
    "tensorflow-probability==0.19.0",
    ...
)
```

## Verify Rebuild

After deploying, check the logs:

```bash
modal app logs ddsp-timbre-transfer
```

You should see pip installing packages, not using cache.

## Test Again

```bash
cd modal-ddsp
./quick_test.sh
```
