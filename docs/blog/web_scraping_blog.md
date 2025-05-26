# AI-Powered Municipal Signals: From Meeting Minutes to Market Moves

## Introduction

Municipal engineering firms often operate in a reactive mode when it comes to business development. Requests for Proposals (RFPs) are typically the first sign that a project is on the horizon, leaving firms to compete on speed, price, or reputation—rarely on foresight. But what if it were possible to identify project signals *before* they materialize as formal solicitations?

This post explores a strategic solution: an AI-enhanced system that leverages natural language processing (NLP) and automated web scraping to extract actionable insights from public utility board meeting minutes. By transforming raw transcripts into searchable, highlightable intelligence, firms can position themselves well in advance of RFP announcements.

The pilot case for this approach was JEA, the community-owned utility based in Jacksonville, Florida. Through this proof-of-concept, we developed a fully functional pipeline to collect, analyze, and visualize board meeting documents—revealing early indicators of capital projects long before they hit the public bidding calendar.

## The Problem: Lagging Behind in Business Development

In the traditional model of municipal business development, engineering firms rely heavily on public bid portals and procurement notifications. These signals, while critical, represent the final stages of project planning—well after budgets are approved, scopes are defined, and internal discussions have shaped the project trajectory.

This approach creates two core disadvantages:

1. **Limited Strategic Positioning**: By the time an RFQ is released, it's often too late to influence project scope or build rapport with decision-makers.
2. **Increased Competition**: Public solicitations invite wide participation, leading to higher competition and pressure on fees.

However, municipalities do not operate in secrecy. Major project decisions and discussions are typically reviewed in public meetings, memorialized in the form of board meeting minutes or committee packages. While accessible, these documents are not easily searchable or structured, making them impractical to scan manually at scale.

The result is a missed opportunity. Valuable signals—such as capital allocation discussions, consent agenda approvals, or committee briefings—remain buried in PDFs, overlooked by even the most experienced BD teams.

In a field where timing and preparation define success, identifying these signals early can mean the difference between being first in line or just another respondent in the inbox.

## The Solution: Automating Intelligence Collection

To address this gap, we developed a system to automatically extract, filter, and present high-value insights from municipal meeting minutes—transforming unstructured public records into actionable business intelligence.

The solution is built around three core capabilities:

1. **Targeted Web Scraping**: A custom Python script systematically downloads board meeting minutes and associated packages from the JEA website.
2. **Natural Language Processing**: Using spaCy, the documents are parsed to extract named entities (organizations, locations, monetary figures, dates) and detect project-related keywords.
3. **Visualization and Navigation**: The results are both saved to structured CSV files and presented through an interactive dashboard. Matched PDFs are highlighted and bookmarked for fast review, reducing manual reading time.

This system does not just collect documents—it identifies opportunities hidden within them. By tracking references to stormwater upgrades, lift station replacements, utility infrastructure expansions, and funding approvals, we gain foresight into what may become a future RFQ.

## How We Built It: From Concept to Working System

The development process began with a clear hypothesis: that municipal meeting minutes contain early-stage project references which could be programmatically extracted and used to improve business development strategy.

Our initial approach was exploratory—writing a basic scraper to collect and save PDFs from the JEA website. While functional, it quickly became apparent that downloading documents alone wasn’t enough. We needed a way to extract meaningful signals without reading each file manually.

We then incorporated **keyword matching**, using a configurable text file that allowed us to define terms of interest such as “stormwater,” “lift station,” “rehabilitation,” and “capital improvements.” With this in place, the scraper was updated to scan only the first few pages of each PDF for mentions—minimizing memory usage while increasing relevance.

As our confidence grew, we added **NLP features** using the spaCy library. This allowed the system to extract named entities such as contractor names, cities, and dollar amounts. We also integrated PyMuPDF to highlight keyword matches directly inside the PDFs and create outline bookmarks for each mention, making the documents easier to navigate.

To enhance usability, we built a **dashboard using Streamlit**, allowing users to:

* Filter matches by keyword or entity type
* Sort and search the extracted mentions
* Review snippets in context
* Access the corresponding annotated PDF

## INSERT STREAMLIT IMAGE

Each iteration added efficiency, clarity, and professional polish to the system. What began as a one-off scraper evolved into a modular intelligence-gathering tool—flexible enough to be repurposed for other utilities or municipalities.

This iterative, feedback-driven approach was key. Rather than attempting to build the perfect system from day one, we allowed the data, use cases, and performance feedback to guide each layer of development. The result is a lightweight yet powerful tool tailored for actionable insights in the civil infrastructure space.

## What We Found

After running the system against hundreds of meeting minutes spanning multiple years, several patterns began to emerge—patterns that would be difficult, if not impossible, to identify manually.

1. **Committee-Level Signals**: The most relevant discussions frequently appeared in Finance, Capital Projects, and Governance committees—well before making their way to formal board approval.
2. **Consent Agenda Blind Spots**: Items placed on consent agendas rarely detail the full scope of work in the meeting minutes. However, the full packages often contained exhibits, capital expenditure breakdowns, or naming of potential vendors—critical for pre-positioning.
3. **Emerging Trends**: Projects related to resiliency, stormwater reuse, and system hardening appeared with increasing frequency. Early identification of these themes enables firms to refine pursuit strategies accordingly.
4. **Lead Time Advantage**: On multiple occasions, we identified discussions of infrastructure upgrades three to six months before a related RFQ was posted. In a competitive BD environment, that head start can translate into stronger proposals and better client relationships.

These insights aren’t just interesting—they’re actionable. They provide a roadmap for proactive outreach, strategic staffing, and even early teaming opportunities with subconsultants and suppliers.

Rather than reacting to public postings, firms using this approach can anticipate them—and that subtle shift makes all the difference.

## Real-World Impact

The ability to extract insights from board meeting minutes has immediate and tangible value for firms operating in the municipal infrastructure sector. Some of the key advantages realized through this project include:

* **Increased Visibility**: By uncovering potential project mentions in advance, our business development team can proactively reach out to potential clients with relevant experience, case studies, and solutions.
* **Improved Strategic Planning**: The data provides directional insight on where funding is being allocated, which infrastructure types are gaining attention, and which departments or committees are most influential.
* **Time Savings**: Highlighted PDFs and entity extraction reduce hours of manual reading and note-taking to minutes of focused review.
* **Competitive Advantage**: Early awareness allows our firm to begin positioning long before a solicitation is released, often leading to stronger proposals, more relevant teaming, and improved client rapport.

This initiative has changed how we think about public data. It is no longer a passive resource—it’s a competitive asset when curated and interpreted effectively.

## Tech Stack

The system is designed to be modular, scalable, and easy to maintain. It was developed using the following tools:

* **Python** – Core programming language for scripting and automation
* **pdfplumber** – Text extraction from structured PDF documents
* **PyMuPDF (fitz)** – PDF highlighting and annotation
* **spaCy** – Named Entity Recognition and NLP processing
* **BeautifulSoup4** – Web scraping and HTML parsing
* **pandas** – Data cleaning and CSV export
* **Streamlit** – Lightweight web dashboard for exploring extracted matches
* **conda** – Environment management and dependency control

This tech stack supports both technical extensibility and usability for non-technical team members.

## What’s Next

This project laid the groundwork for a new approach to business development, but several opportunities for expansion remain:

* **Summarizing Packages**: Currently, our tool focuses on minutes. Extending it to parse and summarize attached board packages (often much longer) could surface even more detailed insights.
* **ML Classification**: Incorporating basic machine learning to classify mentions by urgency or likelihood of resulting in an RFP would help prioritize outreach efforts.
* **Alerting System**: We plan to integrate keyword or entity-based alerts through email to notify BD teams in real time.
* **CRM Integration**: Linking extracted data to internal CRM tools would allow mentions to be tracked as early-stage leads, complete with follow-up scheduling.
* **Multi-Agency Scaling**: The structure of this tool allows it to be easily configured to monitor additional municipal utilities or agencies, broadening the insight base significantly.

Each of these improvements would deepen the system’s impact while maintaining its original design philosophy: to surface the unsurfaced and give our team the edge.

## Final Thoughts

In an era where data is abundant but attention is scarce, the firms that succeed are those who learn to see clearly—earlier and faster than their peers. Municipal board meetings may not make headlines, but for those who know where to look, they offer a window into the future.

By pairing automation with analysis, this system transforms public documents into strategic intelligence. It doesn’t just streamline research—it enhances decision-making.

For engineering firms that want to do more than respond, this is how you begin to lead.
