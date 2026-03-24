# 🛡️ Intruder Detection System (Microservices + Edge/Cloud)

> MSc Dissertation Project – Real-time AI-based intrusion detection using Raspberry Pi, Docker, and AWS

---

## 📌 Overview  
This project presents a real-time intruder detection system developed using a containerized microservices architecture, deployed across both edge (Raspberry Pi) and cloud (AWS EC2) environments.  

The system integrates IoT hardware, machine learning, and cloud services to detect and notify potential intrusions efficiently. It also evaluates the performance trade-offs between monolithic and microservices architectures.

---

## 🎯 Objectives  
- Design and implement a smart intruder detection system  
- Compare monolithic vs microservices architectures  
- Evaluate performance across edge and cloud deployments  
- Analyse system efficiency using monitoring tools  

---
## ⚙️ Technologies Used  

- Python (Flask) – Microservices APIs  
- Docker & Docker Compose – Containerization  
- Raspberry Pi 4 + ESP32 + PIR Sensor – Hardware  
- TensorFlow Lite & YOLOv11 – Machine Learning  
- AWS EC2 & S3 – Cloud Infrastructure  
- Prometheus & Grafana – Monitoring

---

## System Architecture  

The system operates in the following pipeline:
1. PIR Sensor + ESP32 → Detect motion  
2. Raspberry Pi → Capture images  
3. Cloud (AWS S3 + EC2) → Process images  
4. Machine Learning Models → Detect intruder  
5. Notification + LED → Alert user  

### Microservices:
- Motion Listener Service  
- Image Capture Service  
- Upload Service  
- Detection Service  
- Notification Service  
- Trigger (LED) Service  

---

## 🧠 Machine Learning Models  

- **MobileNet SSD (TFLite)**  
  - Used for initial human detection
- **YOLOv11s (Custom-trained, TFLite)**  
  - Used for intruder classification (Jason vs Intruder)  

- Exported using TensorFlow Lite with **int8 quantization** for efficiency  

---

## 🐳 Containerization  

- Each component is developed as an independent microservice  
- All services are containerized using Docker  
- Docker Compose is used to manage and run all service

---

## ☁️ Cloud Services  

- **AWS EC2** → Cloud-based detection processing  
- **AWS S3** → Image storage  

---

## 📊 Monitoring & Evaluation  

- **Prometheus** → Collect system metrics  
- **Grafana** → Visualize CPU, memory, and network usage  
- **Node Exporter & cAdvisor** → System and container monitoring  
- **Python logging** → Latency measurement  
- **I2C (UPS Module)** → Power consumption monitoring

---
## 👤 Author  

**Hpone Myat Min**  
MSc Advanced Computer Science 
Leeds Beckett University  
