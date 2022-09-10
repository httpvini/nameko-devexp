RESOLVER:=/etc/resolv.conf

NS_EPINIO:=epinio
APP_EPINIO:=epinio
EPINIO_CHART:=epinio/epinio

# cert-manager is a requirement for Epinio
NS_CERT:=cert-manager
APP_CERT:=cert-manager
CERT_CHART:=jetstack/cert-manager

setup:
	helm repo add jetstack https://charts.jetstack.io
	helm repo add epinio https://epinio.github.io/helm-charts
	helm repo update
install:
	helm install ${APP_CERT} --namespace ${NS_CERT} ${CERT_CHART} \
	--set installCRDs=true --create-namespace \
	--set extraArgs[0]=--enable-certificate-owner-ref=true
	helm install ${APP_EPINIO} -n ${NS_EPINIO} --create-namespace ${EPINIO_CHART} \
	--values values.yaml
upgrade:
	helm upgrade ${APP_EPINIO} -n ${NS_EPINIO} ${EPINIO_CHART} \
	--values values.yaml
uninstall:
	helm uninstall -n ${NS_CERT} ${APP_CERT}
	kubectl delete ns ${NS_CERT}
	helm uninstall -n ${NS_EPINIO} ${APP_EPINIO}
	kubectl delete ns ${NS_EPINIO}
status:
	@echo "Checking ${APP_CERT}..."
	@helm list -n ${NS_CERT}
	@echo "Checking ${APP_EPINIO}"
	@helm list -n ${NS_EPINIO}
dnsmagic:
	sudo apt-get update && sudo apt-get install -y dnsmasq
	sudo cp -i -v dnsmasq.conf
	sudo systemctl restart dnsmasq
	sudo systemctl status dnsmasq
	sudo sed -i -e 's/^nameserver/#nameserver' ${RESOLVER}
	sudo sed -e '/^nameserver\s127.0.0.1/d' ${RESOLVER}
	sudo echo 'nameserver 127.0.0.1' >> ${RESOLVER}
