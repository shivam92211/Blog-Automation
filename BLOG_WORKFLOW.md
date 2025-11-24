# Blog Automation Workflow

This document outlines the complete, automated workflow for generating and publishing blog posts. The system is driven by two main scheduled jobs.

### The Two Automated Jobs
The system relies on two separate jobs that run on a schedule:
1.  **Weekly Topic Generation:** Decides *what* to write about.
2.  **Daily Blog Publishing:** *Writes and publishes* the article.

---

### Part 1: Weekly Topic Generation (Runs Once a Week)

This job's purpose is to fill a queue with 7 unique and relevant blog topics for the upcoming week.

1.  **Select a Category:** The job starts by choosing a content category (e.g., "AI & Machine Learning"). To keep content fresh, it intelligently picks the category that has been waiting the longest since it was last used.





2.  **Gather Context:** To generate high-quality topics, the job gathers two types of context:
    *   **News Context:** It fetches the latest technology news headlines from the **NewsData.io** service. This ensures the generated topics are timely and relevant to current trends.
    *   **Historical Context:** It looks at all topics generated in the last 6 months to create a list of what has already been covered, preventing duplicate content.

3.  **Generate Topics via AI:**
    *   A detailed prompt is sent to the **Google Gemini API** (`gemini-2.5-flash` model).
    *   This prompt contains the chosen category, the trending news headlines, the list of topics to avoid, and a request for 7 unique blog ideas with a specific title, description, and keywords.

4.  **Validate and Schedule:**
    *   The AI returns a list of 7 topics.
    *   The job checks these new topics against the historical ones to ensure they are unique.
    *   Each valid topic is assigned a publication date for the upcoming week (e.g., Tuesday, Wednesday, Thursday...).
    *   These topics are then saved to the database with a status of **"pending"**.

### Part 2: Daily Blog Publishing (Runs Every Day)

This job takes one topic from the queue, writes a full article, and publishes it.

1.  **Fetch Today's Topic:** The job wakes up and queries the database for a topic that is scheduled for the current date and has a status of **"pending"**. If no topic is found, the job simply stops.

2.  **Generate Blog Content via AI:**
    *   If a topic is found, its status is changed to **"in_progress"**.
    *   A new, highly detailed prompt is sent to the **Google Gemini API**. This prompt includes the topic title, keywords, and instructions on the desired word count (1200-1500 words), writing style, Markdown formatting, and SEO best practices.
    *   Gemini generates and returns a complete article, including a final title, the content in Markdown, a meta description, and SEO tags.

3.  **Generate and Upload Cover Image:**
    *   A third call is made to the **Gemini Image Model** (`gemini-2.5-flash-image`) with a prompt to create a professional, abstract cover image related to the blog's title.
    *   The generated image is saved as a temporary file.
    *   This temporary file is then uploaded to an image hosting service (currently Imgur) to get a public URL.

4.  **Publish to Hashnode:**
    *   The job now connects to the **Hashnode API**.
    *   It sends the full blog content, the final title, tags, and the public URL of the cover image to be published on your blog.

5.  **Finalize and Clean Up:**
    *   Once Hashnode confirms the post is live, it returns the URL of the new article.
    *   The job updates the blog's status in the database to **"published"** and saves the Hashnode URL.
    *   The original topic's status is updated to **"completed"**.
    *   The temporary image file created in step 3 is deleted.

If any step in this daily job fails, the topic's status is set to **"failed"**, and the error is logged so you can investigate or retry it manually.
