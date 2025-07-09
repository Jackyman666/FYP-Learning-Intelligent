# Final Year Project — Learning Intelligent Platform

🎓 Welcome! This project is developed as part of my Final Year Project (FYP), aiming to generate HKDSE English Reading Mock Papers intelligently.

This package includes all code, documentation, presentation slides, and final report related to my FYP submission.

---

## 📦 What's Included

- Full source code (FastAPI backend, Next.js frontend)
- Documentation files
- Presentation slides (PDF)
- Final written report (PDF)
- `.env` file (for testing purpose — see security notice)

---

## 🚀 How to Use

### Start the Pipeline

To generate a complete mock paper, call the `/generate` API endpoint.

Example request (POST):

```
POST /generate
Content-Type: application/json
{
  "your_parameters_here": "..."
}
```

This will automatically start the full paper generation pipeline.

---

### Testing Individual Functions

If you want to test individual functions separately (such as generation, formatting, uploading), you can call those endpoints directly.

⚠️ After testing individual functions, please remember to manually delete any temporary files or cache to avoid conflict or duplication.

---

### Environment Variables

- A `.env` file is included in this submission for testing and demonstration purposes.
- 📢 Important: Please keep the `.env` file secure. It may contain API keys or sensitive configuration details.

---

### Live Demo Available

For the easiest experience, you are highly recommended to try the system through the deployed website:

👉 https://fyp-learning-intelligent.vercel.app/

- The frontend allows you to input requirements and automatically trigger the generation pipeline.
- The backend services are connected and running live.

---

### Access Latest Code Updates

As this project may continue to be updated and improved even after submission, you can always access the latest version of the code from the GitHub repository:

👉 https://github.com/Jackyman666/FYP-Learning-Intelligent

---

## 🔒 Security Notice

- Do not share or publish the `.env` file.
- API keys and sensitive data inside `.env` are for educational use only.

---

## 📄 Additional Notes

- This zip file contains all essential deliverables required by my FYP submission.
- Source code is organized clearly into backend and frontend folders.
- Documentation includes system design, architecture diagrams, and implementation details.
- Presentation slides summarize the project goals, workflow, results, and improvements.

---

## 🛠️ Technology Stack

- Backend: Python (FastAPI)
- Frontend: TypeScript (Next.js)
- Database/Cache: Azure Redis
- Deployment: Vercel (Frontend), Azure (Backend)

---

## 🙏 Thank You

Thank you for reviewing my FYP submission.  
I hope you enjoy exploring the Learning Intelligent platform!

If you have any questions, feel free to reach out.
