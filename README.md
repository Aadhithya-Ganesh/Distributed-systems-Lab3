### Distributed systems LAB 3

The purpose of this lab is to design, deploy, and evaluate a resilient microservices-based system using modern distributed systems practices. The focus is on implementing and analysing fault tolerance techniques that enable applications to remain stable and responsive in the presence of failures.

---

### Prerequisites

Ensure you have Minikube and kubectl installed before proceeding. You can download it here:

[Minikube install guide](https://kubernetes.io/docs/tutorials/hello-minikube/)
[Kubectl install guide](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/)

---

### Running the application

1. **Start minikube cluster**
   ```bash
   minikube start
   ```
2. **In the root directory, start deployments and services**
   ```bash
   kubectl apply -f deployments.yaml -f service.yaml
   ```
3. **For check the output, run the below command and visit localhost:80**
   ```bash
   kubectl port-forward svc/web-app-service 80:80
   ```
4. **For running the chaos experiment**
   ```bash
   cd chaos
   ```
   ```bash
   chaos run experiment.json
   ```

---

### Frontend endpoints

Your client service is exposed at:
http://localhost:80
(after running: kubectl port-forward svc/web-app-service 80:80)

| Endpoint       | Purpose                                                | Query Params                                 | Backend Up (Expected Result)                   | Backend Down (Expected Result)                                          |
| -------------- | ------------------------------------------------------ | -------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------- |
| `GET /`        | Basic health check                                     | None                                         | 200 OK: `{ "message": "Hello" }`               | Only fails if client is down                                            |
| `GET /circuit` | Demonstrates Circuit Breaker pattern                   | `mode=chaos` → routes to `/chaos` on backend | Returns 200 with backend response              | First 1–2 calls → 500 errors, then **503 fast-fail** once breaker opens |
| `GET /retries` | Demonstrates Retries with Exponential Backoff + Jitter | `mode=chaos` → routes to `/chaos` on backend | Returns 200, includes time taken + delays list | Performs up to 5 retries, then returns **500**, includes delays used    |
