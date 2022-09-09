NS:=epinio
APP_NAME:=epinio
CHART:=epinio/epinio
RESOLVER:=/etc/resolv.conf

install:
	helm install ${APP_NAME} -n ${NS} --create-namespace ${CHART} \
	--values values.yaml
upgrade:
	helm upgrade ${APP_NAME} -n ${NS} ${CHART} --values values.yaml
uninstall:
	helm uninstall -n ${NS} ${APP_NAME}
	kubectl delete ns ${NS}
status:
	helm list -n ${NS}
dnsmagic:
	sudo apt-get update && sudo apt-get install -y dnsmasq
	sudo cp -i -v dnsmasq.conf
	sudo systemctl restart dnsmasq
	sudo systemctl status dnsmasq
	sudo sed -i -e 's/^nameserver/#nameserver' ${RESOLVER}
	sudo sed -e '/^nameserver\s127.0.0.1/d' ${RESOLVER}
	sudo echo 'nameserver 127.0.0.1' >> ${RESOLVER}
