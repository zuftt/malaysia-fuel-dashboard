from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import CloudFront, APIGateway, VPC
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS, Dynamodb
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudwatch, SystemsManager, Cloudtrail
from diagrams.aws.security import KMS, WAF, IAMRole
from diagrams.aws.integration import SNS, Eventbridge
from diagrams.aws.compute import ECR
from diagrams.onprem.client import Users
from diagrams.onprem.vcs import Github

graph_attr = {
    "fontsize": "24",
    "fontname": "Helvetica Bold",
    "bgcolor": "#ffffff",
    "pad": "0.6",
    "nodesep": "0.7",
    "ranksep": "0.9",
    "label": "Malaysia Fuel Dashboard — Serverless 3-Tier AWS Architecture",
    "labelloc": "t",
    "labeljust": "c",
}

node_attr = {"fontsize": "10", "fontname": "Helvetica"}
edge_attr = {"fontsize": "8", "fontname": "Helvetica", "color": "#888888"}

with Diagram(
    "",
    filename="/Users/muhdzafri/fuel-price-dashboard/malaysia-fuel-dashboard/projects/malaysia-fuel-dashboard/infra/aws_architecture",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    outformat="png",
):
    users = Users("Users")
    github = Github("GitHub Actions\n(OIDC — no keys)")

    waf = WAF("AWS WAF\nRate Limit + OWASP")
    cdn = CloudFront("CloudFront\nCDN + HTTPS")

    users >> Edge(label="HTTPS") >> waf >> cdn

    s3 = S3("S3\nStatic Frontend\n(versioned + KMS)")
    apigw = APIGateway("API Gateway\nHTTP API")

    cdn >> Edge(label="/* static") >> s3
    cdn >> Edge(label="/api/*") >> apigw

    with Cluster("VPC — ap-southeast-1\nPublic + Private Subnets"):

        with Cluster("Private Subnets (Lambda + RDS)"):
            api_lambda = Lambda("API Lambda\nFastAPI + Mangum")
            scraper_lambda = Lambda("Scraper Lambda\nWeekly Sync")
            rds = RDS("RDS PostgreSQL 16\nMulti-AZ · KMS")

        apigw >> api_lambda
        api_lambda >> Edge(label="port 5432") >> rds
        scraper_lambda >> Edge(label="write") >> rds

    # Event-driven
    eb = Eventbridge("EventBridge\nWed 6PM MYT")
    sns = SNS("SNS\nPrice Alerts")
    ddb = Dynamodb("DynamoDB\nSubscriptions\n+ Visitor Counter")

    eb >> Edge(label="cron") >> scraper_lambda
    scraper_lambda >> Edge(label="notify") >> sns
    api_lambda >> Edge(label="read/write", style="dashed") >> ddb

    # Security & Ops
    with Cluster("Security & Monitoring"):
        kms = KMS("KMS CMK")
        trail = Cloudtrail("CloudTrail")
        ssm = SystemsManager("SSM Secrets")
        cw = Cloudwatch("CloudWatch\nDashboard\n+ Alarms")
        iam = IAMRole("IAM\nLeast Privilege\n+ OIDC")

    ecr = ECR("ECR\n2 Repos")

    github >> Edge(label="push", style="dashed") >> ecr
    github >> Edge(label="sync", style="dashed") >> s3
    ecr >> Edge(label="pull", style="dashed") >> api_lambda
