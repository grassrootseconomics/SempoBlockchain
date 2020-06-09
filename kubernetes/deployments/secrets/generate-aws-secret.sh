#!/bin/sh
set -o errexit -o nounset -o pipefail

cat <<EOF | kubectl apply -n $NAMESPACE -f -
apiVersion: v1
kind: Secret 
metadata:
  name: aws
type: Opaque
data:
  AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
  SECRETS_BUCKET: $SECRETS_BUCKET
---
EOF