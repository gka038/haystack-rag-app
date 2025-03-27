# Haystack RAG sample app
This application is deployed as a helm chart on Orbstack to test this application locally. 

## Pre-requisites

* [Orbstack](https://orbstack.dev/) or Docker Desktop
* npm 
* helm

## Deploy Application 

I created one master chart that installs everything for simplicity. 
It has indexing-service, query-service, frontend, opensearch as well as nginx-ingress-controller packed into one.

All of them (except ingress controller) use custom templates located at [helm-template](./helm-template). The master [Chart.yaml](./haystack-rag-masterchart/Chart.yaml) contains all dependencies with repo location and I use alias to better manage their values.
The master chart also has some templates for common resources like configmap, ingress and PVC.

The [values](./haystack-rag-masterchart/values.yaml) file in master chart has all values that can be changed in one single location.

## Create a publicly available domain using localtunnel

Since the frontend image uses build time arguments which cannot be changed later, I used [localtunnel](https://theboroer.github.io/localtunnel-www/) to create a tunnel on port 8000 where I will port-forward my nginx-ingress controller service.

```
npm install -g localtunnel
lt --port 8000  
```
**Copy the url output of this command. DO NOT close the terminal, but open a new one for next steps.**

## Build the docker images 

I did not change any code for the applications. But I modified the Dockerfiles to run as non root user for security and added multistage builds to reduce image size. Make sure to copy the same URL from previous command as the build arg

```
LOCAL_TUNNEL_URL="https://empty-tools-tan.loca.lt"  ## change to the value of your tunnel 
IMAGE_TAG=test1
docker build -t frontend:$IMAGE_TAG --build-arg REACT_APP_HAYSTACK_API_URL=$LOCAL_TUNNEL_URL  -f frontend/Dockerfile.frontend frontend 
docker build -t query:$IMAGE_TAG -f backend/Dockerfile.query backend
docker build -t indexing:$IMAGE_TAG -f backend/Dockerfile.indexing backend
```

## Install the helm chart and expose the URL

**Add a valid password for opensearch and add the openaiAPI key on the [values file](./haystack-rag-masterchart/values.yaml).**

Modify any feild in the values file if you wish to change.
If you modify the hostname manually, you can skip this step
```
# add the domain name you got from localtunnel into values file (wihtout https)
domain=$(echo "$LOCAL_TUNNEL_URL" | sed 's/https:\/\///')
sed -i '' "1s/.*/hostname: \&hostname $domain/" haystack-rag-masterchart/values.yaml
````

### Pull all helm dependencies and install the chart

```
# change any other values if you want on the values file
helm dep up haystack-rag-masterchart
helm upgrade --install haystack-rag-masterchart haystack-rag-masterchart
```

Wait for all pods to start. Now you can port-forward nginx-ingress-controller service

```
k port-forward svc/nginx-ingress 8000:80
```
and visit the LOCAL_TUNNEL_URL on your browser. You might be asked for a password. Add the output of the following command as the password (usually IP address is the password)

```
curl https://loca.lt/mytunnelpassword
```

This $LOCAL_TUNNEL_URL is now avialable on the internet for anyone to use. You can share this link and password to any user and they can open it on their laptop.
The major advantage of this is no need to configure any ssl certs but still can use https, while also sharing your application to anyone over internet till you close the tunnel.
I used this instead of grok because the public URL is needed at build time for the frontend dockerfile


### things to note 

I used localPath for storage and pipeline PVC because they needed to be shared between pods and the default storageclass did not allow readwritemany accessmode.

The opensearch pvc is still using the default storageclass since its used by only one pod.


# Bonus Points

## Airgapped deployment.
1. Usually used in super secure systems with no internet/outbound access
2. While its very secure, regular operations like backup, security patches etc.. become hard to deploy
3. Dependencies of any applications/security patches also needs to be included in the upgrade package.
4. The application must be designed to not have any runtime dependencies like pulling new version or installing a package at runtime.
5. Access to this system must be kept more secure since it becomes the only point of entry to the deployment and even a minor security issue here could compromise the entire system.

## Integration with alternative password store solution. (external-secrets operator, Hashicorp Valuts, SOPS)
1. Keeping secrets in one of AWS SSM/secrets manager, Hashicorp vault etc.. makes our deployment mannifests easier to manage since they dont contain any sensitive information.
2. This is especially usesful for gitops approach since even the deployment tool does not have access to the sensitive information. This also eliminates the secret management from the entire CI-CD pipeline. 
3. The external-secrets-operator can be consigured to any secret store and with right permissions can fetch those. If they are in EKS, then using IRSA an IAM role can be assigned to a serviceAccount which will be assigned to the operator to fetch the secrets at runtime. 
4. There is also an option to sync the secrets at regular intervals which make sure the secret store becomes the sigle point to rotate them.
5. The secrets created by the operator can then be used as regular secrets in the deployments. It can also be configured to fetch multiple secrets using regex.



## Monitoring and logging integration (Prometheus, Grafana, Loki, ELK Stack).

1. I have worked with Grafana Labs stack - Mimir, Loki, Tempo, Grafana, Grafana-alloy along with fluentbit. It is compatible with prometheus metrics so we can reuse most of the CRDs like serviceMonitor (fetch metrics from an endpoint), PrometheusRules (alerts), prometheus-pushgateway, adapter etc.. 
2. They have proven to work at extremely large scale. The storage type for these can be simple object store like s3, keeping the costs low. 
3. Also these are opensource tools and quite easy to manage and self host. Since grafana is the defacto standard for visualization, it is easier to stay in the same ecosystem. 
4. I used fluentbit because I could configure lua scripts to get more pod labels before pushing them to loki. Also this avoids grafana-alloy being the single point of failure for the monitoring system.

