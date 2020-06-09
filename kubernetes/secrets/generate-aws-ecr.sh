kubectl create secret generic aws-ecr \
    --from-file=.dockerconfigjson=$HOME/.docker/aws-config.json \
    --type=kubernetes.io/dockerconfigjson