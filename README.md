# Graph Visualiser

Graph Visualiser is a modular platform for loading, processing and visualizing graph data structures.  
The system is designed using a **plugin architecture** which allows easy extension with new data sources and visualization techniques.

The application supports multiple graph data formats and multiple visualization approaches through dynamically installed plugins.

# Team members

- SV5/2023 – Marko Pavlovic  
- SV46/2023 – Vukasin Vitomirovic  
- SV47/2023 – Ognjen Miletic  
- SV49/2023 – Ognjen Vujovic  
- SV80/2023 – Aleksandar Papic  

---

# Project Architecture

The project is organized into several components:

- **Platform** – core functionality for graph manipulation and plugin communication  
- **API** – abstraction layer defining the graph data model and plugin interfaces  
- **Data source plugins** – responsible for parsing input data and constructing graphs  
- **Visualizer plugins** – responsible for rendering graph structures  
- **Web applications** – user interface for interacting with the platform

The system currently includes plugins for:

- JSON graph loading
- CSV graph loading
- XML graph loading
- Simple graph visualization
- Block graph visualization

---

# Installation

Before running the application, all dependencies must be installed.

Open a terminal in the **root directory of the project** and run: **.\install.bat**

This script performs the following steps automatically:

1. Creates a **Python virtual environment (`.venv`)** if it does not already exist.
2. Activates the virtual environment.
3. Upgrades **pip** to the latest version.
4. Installs all platform modules in **editable mode**:
   - `api`
   - `platform`
   - `json-plugin`
   - `csv-plugin`
   - `xml-plugin`
   - `simple-visualizer`
   - `block-visualizer`
5. Installs required web frameworks:
   - **Django**
   - **Flask**

After the script finishes, all required dependencies for the platform and web applications will be installed inside the virtual environment.

---

# Running the Applications

The project contains **two web applications**:

- Django web application
- Flask web application

After running the installation script, you can start either of them.

---

# Running the Django Application

Navigate to the Django project directory: **cd graph-explorer-Django**

Start the Django development server: **python manage.py runserver**

The application will be available at: **http://127.0.0.1:8000**


---

# Running the Flask Application

Navigate to the Flask project directory: **cd graph-explorer-flask**

Run the Flask application: **python app.py**

The Flask application will start on its configured port  **`http://127.0.0.1:5000`**.

---

# Project Structure

graph-visualiser
│
├─ api
│
├─ platform
│
├─ json-plugin
├─ csv-plugin
├─ xml-plugin
│
├─ simple-visualizer
├─ block-visualizer
│
├─ graph-explorer-django
│
├─ graph-explorer-flask
│
├─ install.bat
│
└─ README.md

