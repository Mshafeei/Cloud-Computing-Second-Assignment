#!/bin/bash

set -u

IMAGE="${1:-}"

Layers=("sha256:37fb86c2a767b88d500c6872195f88078f64765fe0d2f9cc375cc2efbd4c0a41"
        "sha256:68bced9e0afa4479df17c3646e27c7c7e9ce9ba70c0e6c73b6826487b89037d9"
        "sha256:2dc99d2d0a39fce31e37615eb4c932e16dcc4c2b0ce9993714280081b5dbe085"
        "sha256:05e0eee5572e9c9f50408a2132590133b830a668a1cf2ff2b150f19c57707e2b"
        "sha256:c5deb3dcd959bc993bfb363b6e6c1a0d9b1f30b5366d4b8e5e30c694c5a5a75f"
)

LAYERS=(
    "sha256:dd57f90311a2567b55ff22eeacff1602fd04ad7566e315957731359eab173b90"
    "sha256:3dc3efdf011007403514ffd3b699da9deef847535ae30a3639ef3fee93c1375e"
    "sha256:96a69f98ae076bdff5264720ee922820291d658c6a2df97f7c4899864ceb7ea8"
    "sha256:340931a1d98607a7f1319082179f82ba477f1a1de6e3ecf2ea11f4cc0fe454c3"
    "sha256:b0280c7126def7a5d82eb76438bb8ba3dd88eaa9292c12e17e3e6d97ad471614"
    "sha256:902e79dc215dd999d78605464baf3bd69347ffcc12acc91cd501afcb6ba034a2"
)

FOUND=0
ERRORS=0

echo "======================================"
echo " Checking Docker Image for secret.txt"
echo "======================================"

# 1. Check all image layers
echo "[1] Checking image layers..."

for layer in "${Layers[@]}"; do

    hash="${layer#sha256:}"
    file="safe-layers/blobs/sha256/$hash"

    echo
    echo "Checking layer: $hash"

    if [[ ! -f "$file" ]]; then
        echo "[ERROR] Layer file not found: $file"
        ERRORS=1
        continue
    fi

    contents=$(tar -tf "$file" 2>/dev/null)

    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Could not read layer archive."
        ERRORS=1
        continue
    fi

    matches=$(echo "$contents" | grep -E '(^|/)secret\.txt$|(^|/)\.wh\.secret\.txt$' || true)

    if [[ -n "$matches" ]]; then
        echo "[FOUND] Relevant entries:"
        echo "$matches"
        FOUND=1
    else
        echo "[OK] No secret.txt entries found."
    fi

done

# 2. Check Docker image inspect
echo
echo "[2] Checking Docker image inspect..."

if [[ -z "$IMAGE" ]]; then
    echo "[SKIPPED] No image name provided."
else
    inspect=$(docker image inspect "$IMAGE" 2>&1)

    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Could not inspect image."
        ERRORS=1
    elif echo "$inspect" | grep -Fiq "cloud-hw2-demo-secret-DO-NOT-USE"; then
        echo "[FOUND] cloud-hw2-demo-secret-DO-NOT-USE referenced in image inspect."
        FOUND=1
    else
        echo "[OK] No cloud-hw2-demo-secret-DO-NOT-USE reference in image inspect."
    fi
fi

# 3. Check Docker image history
echo
echo "[3] Checking Docker image history..."

if [[ -z "$IMAGE" ]]; then
    echo "[SKIPPED] No image name provided."
else
    history=$(docker history --no-trunc "$IMAGE" 2>&1)

    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Could not retrieve image history."
        ERRORS=1
    elif echo "$history" | grep -Fiq "cloud-hw2-demo-secret-DO-NOT-USE"; then
        echo "[FOUND] cloud-hw2-demo-secret-DO-NOT-USE referenced in image history."
        FOUND=1
    else
        echo "[OK] No cloud-hw2-demo-secret-DO-NOT-USE reference in image history."
    fi
fi

# 4. Final result
echo
echo "======================================"
echo "              SUMMARY"
echo "======================================"

if [[ $FOUND -eq 0 && $ERRORS -eq 0 ]]; then
    echo "[PASS] No secret.txt filename references found."
elif [[ $FOUND -eq 1 ]]; then
    echo "[FAIL] secret.txt references were found."
else
    echo "[INCOMPLETE] Some checks could not be completed."
fi