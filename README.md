# ♻️ Mechanical Compost Tumbler - Decision Support System (DSS)

**📌 Academic Transparency Note for Instructors:** 
*This repository and the accompanying Decision Support System (DSS) are developed exclusively for the review of the MUH401 Interdisciplinary Capstone Project instructors. Artificial Intelligence (AI) tools were utilized as an assistive technology in structuring the Streamlit UI code, optimizing data visualization, and formatting this documentation.*

This repository contains the source code for the Streamlit-based DSS developed at Hacettepe University. It serves as an integrated capacity planning, mechanical constraint monitoring, and production scheduling tool, bridging Mechanical Engineering (ME) design parameters with Industrial Engineering (IE) operational models.

## 🚀 Key Modules & Interdisciplinary Integration

### Mechanical Engineering (ME) Constraints
* **ME-1: Tumbler Maximum Capacity:** Integration of the tumbler's volumetric and structural limits (e.g., 250 kg max mass load).
* **ME-2: Aeration & Rotational Dynamics:** Mechanical constraints governing the turning frequency and aerobic airflow required for the 21-day cycle.
* **ME-3: Mass Balance & Final Yield:** Process efficiency modeling that calculates the final compost harvest (e.g., 60% remaining mass) after the aerobic degradation process.

### Industrial Engineering (IE) Optimization
* **IE-1: Capacity Planning:** Dynamic calculation of required tumbler units based on daily organic waste volume (SKS portion data) and ideal C:N ratio optimization.
* **IE-2: Production Scheduling:** Automated 21-day Gantt chart generation for continuous sequential batch tracking and operator task management.
* **IE-3: Financial Analysis (ROI):** Real-time CAPEX (Initial Investment) vs. operational savings tracking and amortization forecasting.

## 🛠️ Tech Stack
* **Frontend/Backend:** Python, Streamlit
* **Database:** SQLite
* **Data Visualization:** Plotly, Pandas

## ⚙️ How to Run Locally
1. Clone this repository: `git clone https://github.com/your-username/your-repo-name.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

*Project Leader: Yusuf Bora Çavdar | Interdisciplinary Engineering Team*
