#  Ekstraklasa Predictor

A machine learning application that predicts Polish Ekstraklasa football match outcomes using historical data from 25 seasons.

**INPUT:** 2 teams  
**OUTPUT:** Win probability (%) and predicted winner

---

##  Project Overview

This project consists of three main components:
- **Scraper**: Collects historical match data from FlashScore.pl
- **Database**: Stores team information and match statistics in PostgreSQL
- **ML Model**: Predicts match outcomes using Random Forest Classifier

---

##  Technology Stack

- **Python 3.8+**
- **Web Scraping**: Playwright
- **Database**: PostgreSQL
- **Machine Learning**: scikit-learn (Random Forest Classifier)
- **Data Processing**: polars, numpy
- **Additional**: sqlalchemy, psycopg2

---

## UML schema of Database


![UML SCHEMA OF DB](home/monerl/Projekty/ekstraklasa_predictor/pictures/database_schema.png)