# Real Estate Multi-Agent System (ADK Hackathon Submission)

![Architecture Diagram](./ADK%20-%20Hackathon.drawio.svg)

## Introduction

This project is a multi-agent AI system built for the [Agent Development Kit Hackathon with Google Cloud](https://googlecloudmultiagents.devpost.com/?utm_source=gamma&utm_medium=email&utm_campaign=FY25-Q2-NORTHAM-GOO34096-onlineevent-su-ADKHackathon&utm_content=innovators-newsletter&utm_term=-). It demonstrates the orchestration of specialized agents to automate real estate data analysis, property intelligence, and report generation using the Agent Development Kit (ADK) and Google Cloud services.

## Features
- **Automated Property Intelligence**: Input a property address and receive a comprehensive, data-driven report.
- **Multi-Agent Collaboration**: Specialized agents (Google Maps, Real Estate Data, Google Search, Report Writer) work together to gather, analyze, and synthesize information.
- **Integration with Google Cloud**: Utilizes Cloud Run for scalable orchestration, Gemini for LLM tasks, and Google Cloud Storage for persistent data.
- **Extensible Architecture**: Easily add new data sources or agent capabilities.

## Architecture

The system is composed of the following agents and services:

- **Google Maps Agent**: Georeferences and normalizes property addresses.
- **Google Search Agent**: Finds public knowledge and news about the property.
- **Real Estate Data Agent**: Aggregates parcel, zoning, and MLS listing data.
- **Report Writer Agent**: Synthesizes findings into a human-readable report.
- **Gemini (LLM)**: Provides advanced reasoning and summarization.
- **Google Cloud Run**: Hosts and orchestrates the agent workflows.
- **Google Cloud Storage**: Stores generated reports and data.

_See the architecture diagram above for a visual overview._

## Technologies Used
- **Agent Development Kit (ADK, Python)**
- **Google Cloud Run**
- **Google Cloud Storage**
- **Gemini (Google LLM)**
- **Google Maps API**
- **Public Parcel Data APIs**
- **MLS Listings APIs**
- **Python, FastAPI, and supporting libraries**

## How it Works
1. **User submits a property address.**
2. **Google Maps Agent** georeferences and normalizes the address.
3. **Real Estate Data Agent** fetches parcel, zoning, and MLS data.
4. **Google Search Agent** gathers public knowledge and news.
5. **Gemini** assists with reasoning, summarization, and data synthesis.
6. **Report Writer Agent** compiles all findings into a comprehensive report.
7. **Report is stored in Google Cloud Storage and returned to the user.**

## Submission Details
- **Demo Video**: https://www.youtube.com/watch?v=lazPWIA-vuM
- **Data Sources**: Google Maps, public parcel data, MLS, Google Search

---

_This project was created for the purposes of entering the ADK Hackathon. #adkhackathon_
