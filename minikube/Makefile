cluster:
	minikube start --driver=docker
	minikube addons enable ingress
	minikube addons enable metallb
	@echo 'Running interactive metallb configuration.'
	@echo -n 'Be sure to use the proper IP ranges during the interactive configuration based on the following IP: '
	@echo $$(minikube ip)
	minikube addons configure metallb
kaboom:
	minikube delete
