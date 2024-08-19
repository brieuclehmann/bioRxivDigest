from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from datetime import date
from python_http_client.exceptions import HTTPError

import argparse
import yaml
import os
from dotenv import load_dotenv
import openai
from relevancy import generate_relevance_score, process_subject_fields
from download_new_papers import get_papers



def generate_body(interest, threshold):
    papers_bio = get_papers("biorxiv")
    papers_med = get_papers("medrxiv")
    papers = papers_bio + papers_med
    if interest:
        relevancy, hallucination = generate_relevance_score(
            papers,
            query={"interest": interest},
            threshold_score=threshold,
            num_paper_in_prompt=16,
        )
        body = "<br><br>".join(
            [
                f'Title: <a href="{paper["main_page"]}">{paper["title"]}</a><br>Authors: {paper["authors"]}<br>Score: {paper["Relevancy score"]}<br>Reason: {paper["Reasons for match"]}'
                for paper in relevancy
            ]
        )
        if hallucination:
            body = (
                "Warning: the model hallucinated some papers. We have tried to remove them, but the scores may not be accurate.<br><br>"
                + body
            )
    else:
        body = "<br><br>".join(
            [
                f'Title: <a href="{paper["main_page"]}">{paper["title"]}</a><br>Authors: {paper["authors"]}'
                for paper in papers
            ]
        )
    return body


if __name__ == "__main__":
    # Load the .env file.
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", help="yaml config file to use", default="config.yaml"
    )
    args = parser.parse_args()
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError("No openai api key found")
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    from_email = os.environ.get("FROM_EMAIL")
    to_email = os.environ.get("TO_EMAIL")
    threshold = config["threshold"]
    interest = config["interest"]
    body = generate_body(interest, threshold)
    with open("digest.html", "w") as f:
        f.write(body)
    if os.environ.get("SENDGRID_API_KEY", None):
        sg = SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        from_email = Email(from_email)  # Change to your verified sender
        to_email = To(to_email)
        subject = date.today().strftime("Personalized bioRxiv and medRxiv Digest, %d %b %Y")
        content = Content("text/html", body)
        mail = Mail(from_email, to_email, subject, content)
        mail_json = mail.get()

        # Send an HTTP POST request to /mail/send
        try:
            response = sg.client.mail.send.post(request_body=mail_json)
        except HTTPError as e:
            print(e.to_dict)
        if response.status_code >= 200 and response.status_code <= 300:
            print("Send test email: Success!")
        else:
            print("Send test email: Failure ({response.status_code}, {response.text})")
    else:
        print("No sendgrid api key found. Skipping email")
