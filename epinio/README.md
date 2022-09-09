# Epinio on Minikube

## Requirements

This setup was validated on Ubuntu Linux 18.04 LTS. It might work on different
Linux distributions.

## "Magic" DNS setup

Per [Epinio documentation](https://docs.epinio.io/installation/magicDNS_setup),
the easiest to configure Epinio "domain name" is to use a external DNS like
SSLIP to proper resolve the domain to the Minikube IP.

In order to properly setup this and still have DNS resolution working properly,
a local setup of dnsmasq is required. See the `dnsmagic` target at the
`Makefile`. The `/etc/resolv.conf` file needs to be changed as well.

Please be aware that the dnsmasq configuration might requires a different value
depending on both Minikube IP address and the DNS server you decided to use.
The default value for such configuration can be reviewed below:

```
server=/192.168.49.2.alceu.org/104.155.144.4
```

Where:

- `192.168.49.2` is the default value returned by the execution of `minikube ip`.
- `alceu.org` is an arbitrary value, anything can be used.
- `104.155.144.4` is the IP address of one of SSLIP DNS servers.

See the `dnsmasq.conf` file for more details.

## Access to Epinio UI

You should be able to open the UI in a browser by accessing:

https://epinio.192.168.49.2.alceu.org

Since the TLS certificate is auto-signed by the Epinio CA, you will see a
warning in the browser that you can safely ignore and add it as an exception.

The default credentials will be:

- user: *admin*
- password: *password*

## Know issues

Currently, not even the
[example application](https://docs.epinio.io/tutorials/single-dev-workflow) can
be deployed to Epinio/Minikube environment.

```
$ kubectl get po -w
NAME                                                              READY   STATUS            RESTARTS   AGE
epinio-server-6b6bb54d7c-wgvd9                                    1/1     Running           0          3h25m
epinio-ui-5d988d8dc7-w4pd6                                        1/1     Running           0          3h25m
helm-controller-b88d89d45-f9wqr                                   1/1     Running           0          3h25m
kubed-7db7bc4765-jwknc                                            1/1     Running           0          3h25m
minio-0                                                           1/1     Running           0          3h25m
registry-bddc87675-2z6pq                                          2/2     Running           0          3h25m
stage-workspace-mysimp-7bed770a4dfef0d1ef97b670ab962dec971lmd2m   0/1     PodInitializing   0          16s
stage-workspace-mysimp-7bed770a4dfef0d1ef97b670ab962dec971lmd2m   0/1     ErrImagePull      0          2m11s
stage-workspace-mysimp-7bed770a4dfef0d1ef97b670ab962dec971lmd2m   0/1     ImagePullBackOff   0          2m26s
```

The Pod logs showed the following:

```
$ kubectl describe po stage-workspace-mysimp-5d21edbc0d40a1839e6de1b993256ba2e15jjjxc
Name:             stage-workspace-mysimp-5d21edbc0d40a1839e6de1b993256ba2e15jjjxc
Namespace:        epinio
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Fri, 09 Sep 2022 14:23:27 -0300
...
Events:
  Type     Reason     Age                 From               Message
  ----     ------     ----                ----               -------
  Normal   Scheduled  5m15s               default-scheduler  Successfully assigned epinio/stage-workspace-mysimp-5d21edbc0d40a1839e6de1b993256ba2e15jjjxc to minikube
  Normal   Pulled     5m12s               kubelet            Container image "amazon/aws-cli:2.0.52" already present on machine
  Normal   Created    5m11s               kubelet            Created container download-s3-blob
  Normal   Started    5m11s               kubelet            Started container download-s3-blob
  Normal   Pulled     5m7s                kubelet            Container image "library/bash:5.1.4" already present on machine
  Normal   Created    5m6s                kubelet            Created container unpack-blob
  Normal   Started    5m6s                kubelet            Started container unpack-blob
  Warning  Failed     52s (x2 over 3m6s)  kubelet            Failed to pull image "paketobuildpacks/builder:full": rpc error: code = Unknown desc = context deadline exceeded
  Warning  Failed     52s (x2 over 3m6s)  kubelet            Error: ErrImagePull
  Normal   BackOff    37s (x2 over 3m5s)  kubelet            Back-off pulling image "paketobuildpacks/builder:full"
  Warning  Failed     37s (x2 over 3m5s)  kubelet            Error: ImagePullBackOff
  Normal   Pulling    25s (x3 over 5m5s)  kubelet            Pulling image "paketobuildpacks/builder:full"
```

The Docker registry credentials were verified with the commands below:

```
kubectl get secret -o jsonpath="{.data['\.dockerconfigjson']}" registry-creds | base64 -d
kubectl port-forward service/registry 5000:5000
docker login localhost:5000
```

Access was granted as expected. The respective Pod is also using the same
credentials.

An attempt to manually download the image was then executed:

```
$ docker image ls | grep paketo
paketobuildpacks/builder                  full               9cefe3e0640a   42 years ago    1.98GB
```

The Docker image is quite large, but that doesn't explain the error. The image,
on the other hand, doesn't look well.

As an additional step, it was attempt to push this same image do the internal
registry:

```
kubectl port-forward service/registry 5000:5000
docker tag paketobuildpacks/builder:full localhost:5000/paketobuildpacks/builder:full
docker image push localhost:5000/paketobuildpacks/builder:full
```

The result was positive:

```
$ curl -u admin -k -X GET https://localhost:5000/v2/_catalog
Enter host password for user 'admin':
{"repositories":["paketobuildpacks/builder"]}
```

An attempt was made to make Epinio to fetch the image from the internal registry
by changing the respective Helm chart configuration:

```yaml
image:
  builder:
    repository: registry:5000/paketobuildpacks/builder
    tag: full
```

But still the same error happens.

As a last attempt, it was attempt to execute a interactive session with the
same image. The Minikube cluster was removed, and reinstalled from scratch,
then the image was used in the following way:

```
$ kubectl run paketo --image=paketobuildpacks/builder:full -- ls -l
pod/paketo created
```

In a different terminal session:

```
$ kubectl get po -w
NAME     READY   STATUS              RESTARTS   AGE
paketo   0/1     ContainerCreating   0          10s
paketo   0/1     ErrImagePull        0          2m2s
paketo   0/1     ImagePullBackOff    0          2m15s
```

On the other hand, executing the image outside the Minikube environment worked
as expected:

```
$ docker container run --rm -ti paketobuildpacks/builder:full ls -l /
total 80
drwxr-xr-x   1 root root 4096 Sep  7 12:12 bin
drwxr-xr-x   2 root root 4096 Apr 24  2018 boot
drwxr-xr-x   1 root root 4096 Sep  9 21:48 cnb
drwxr-xr-x   5 root root  360 Sep  9 21:51 dev
drwxr-xr-x   1 root root 4096 Sep  9 21:51 etc
drwxr-xr-x   1 root root 4096 Sep  9 21:47 home
drwxr-xr-x   2 cnb  cnb  4096 Jan  1  1980 layers
drwxr-xr-x   1 root root 4096 Sep  7 12:12 lib
drwxr-xr-x   2 root root 4096 Sep  2 08:52 lib64
lrwxrwxrwx   1 root root   14 Jan  1  1980 lifecycle -> /cnb/lifecycle
drwxr-xr-x   2 root root 4096 Sep  2 08:51 media
drwxr-xr-x   2 root root 4096 Sep  2 08:51 mnt
drwxr-xr-x   2 root root 4096 Sep  2 08:51 opt
drwxr-xr-x   3 root root 4096 Jan  1  1980 platform
dr-xr-xr-x 361 root root    0 Sep  9 21:51 proc
drwx------   2 root root 4096 Sep  2 08:52 root
drwxr-xr-x   1 root root 4096 Sep  7 12:13 run
drwxr-xr-x   1 root root 4096 Sep  7 12:12 sbin
drwxr-xr-x   2 root root 4096 Sep  2 08:51 srv
dr-xr-xr-x  13 root root    0 Sep  9 21:49 sys
drwxrwxrwt   2 root root 4096 Sep  2 08:52 tmp
drwxr-xr-x   1 root root 4096 Sep  2 08:51 usr
drwxr-xr-x   1 root root 4096 Sep  2 08:52 var
drwxr-xr-x   2 cnb  cnb  4096 Jan  1  1980 workspace
```

The file `epinio/logs/mysimpleapp-2022-09-09T20 10 12` has all the execution
logs until the error from the Pod.

## References

- [Epinio on Minikube](https://docs.epinio.io/howtos/install_epinio_on_minikube)
- [Minio official Docker registry](https://quay.io/repository/minio/minio?tab=tags)
- [Minikube with metalb addon](https://medium.com/@emirmujic/istio-and-metallb-on-minikube-242281b1134b)
- ["Magic" DNS SSLIP](https://sslip.io/)
