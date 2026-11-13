import html

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import settings

router = APIRouter(tags=["Greeting"])

TEAM_MEMBERS = [
    {
        "name": "Nargiz Bayramova",
        "student_id": "TODO-STUDENT-ID",
        "role": "Backend REST API design, PostgreSQL schema modeling, RBAC, and monitoring/Telegram alerts.",
    },
    {
        "name": "Sumaya Gafarova",
        "student_id": "TODO-STUDENT-ID",
        "role": "Project proposal, requirements engineering, AI scheduling logic, and system architecture.",
    },
    {
        "name": "Maryam Aliyeva",
        "student_id": "TODO-STUDENT-ID",
        "role": "Frontend UI/UX design, interactive calendar & dashboard, and client-side state workflows.",
    },
]


def _method_badge_class(method: str) -> str:
    return {
        "GET": "badge-get",
        "POST": "badge-post",
        "PUT": "badge-put",
        "PATCH": "badge-patch",
        "DELETE": "badge-delete",
    }.get(method, "badge-default")


@router.get(
    "/greeting",
    response_class=HTMLResponse,
    summary="Styled HTML overview, team roster, and endpoint directory",
)
async def greeting(request: Request) -> HTMLResponse:
    rows: list[str] = []
    paths = request.app.openapi().get("paths", {})
    for path in sorted(p for p in paths if p.startswith(settings.API_V1_PREFIX)):
        ops = paths[path]
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in ops:
                continue
            op = ops[method]
            desc = html.escape(op.get("summary") or op.get("operationId", ""))
            cls = _method_badge_class(method.upper())
            rows.append(
                f"<tr>"
                f'<td><span class="badge {cls}">{method.upper()}</span></td>'
                f'<td class="mono">{html.escape(path)}</td>'
                f"<td>{desc}</td>"
                f"</tr>"
            )

    team_cards = "\n".join(
        f'<div class="card">'
        f'<div class="member-head"><strong>{html.escape(m["name"])}</strong>'
        f'<span class="id-pill">{html.escape(m["student_id"])}</span></div>'
        f'<p class="muted">{html.escape(m["role"])}</p>'
        f"</div>"
        for m in TEAM_MEMBERS
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>StudyFlow API — Welcome</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --surface: #ffffff;
      --border: #e2e5ef;
      --text: #1e2030;
      --muted: #5c6078;
      --accent: #5553b7;
      --accent-soft: #efeef9;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2rem 1rem;
    }}
    .container {{ max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem; }}
    .hero, .section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.5rem;
      box-shadow: 0 2px 8px rgba(30, 32, 48, 0.04);
    }}
    .hero-top {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }}
    h1 {{ font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }}
    h2 {{ font-size: 1.15rem; font-weight: 600; margin-bottom: 1rem; }}
    .status-pill {{
      display: inline-flex; align-items: center; gap: 0.45rem;
      background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0;
      padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600;
    }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #10b981; }}
    .muted {{ color: var(--muted); font-size: 0.95rem; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }}
    .btn {{
      display: inline-block; text-decoration: none; font-size: 0.875rem; font-weight: 600;
      padding: 0.45rem 0.9rem; border-radius: 8px;
      background: var(--accent-soft); color: var(--accent); border: 1px solid #d9d7f5;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }}
    .card {{ border: 1px solid var(--border); border-radius: 10px; padding: 1rem; background: #fafbfe; }}
    .member-head {{ display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; flex-wrap: wrap; }}
    .id-pill {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.78rem; background: var(--accent-soft); color: var(--accent);
      padding: 0.15rem 0.5rem; border-radius: 6px;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); }}
    th {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; white-space: nowrap; }}
    .badge {{
      display: inline-block; min-width: 62px; text-align: center;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.75rem; font-weight: 700; padding: 0.18rem 0.45rem; border-radius: 6px;
    }}
    .badge-get {{ background: #e0f2fe; color: #0369a1; }}
    .badge-post {{ background: #dcfce7; color: #15803d; }}
    .badge-put {{ background: #fef3c7; color: #b45309; }}
    .badge-patch {{ background: #ede9fe; color: #6d28d9; }}
    .badge-delete {{ background: #fee2e2; color: #b91c1c; }}
    .badge-default {{ background: #f1f5f9; color: #334155; }}
    @media (max-width: 600px) {{
      body {{ padding: 1rem 0.6rem; }}
      .hero, .section {{ padding: 1.1rem; }}
      h1 {{ font-size: 1.4rem; }}
    }}
  </style>
</head>
<body>
  <main class="container">
    <section class="hero">
      <div class="hero-top">
        <h1>StudyFlow API</h1>
        <span class="status-pill"><span class="dot"></span> API Running &bull; v1 ({html.escape(settings.VERSION)})</span>
      </div>
      <p class="muted">
        <strong>StudyFlow</strong> is an AI-powered academic planner and workload balancer built for university students.
        It centralizes enrolled courses, assignments, exams, and weekly study availability, and generates realistic
        daily study schedules while protecting against deadline overload.
      </p>
      <div class="links">
        <a class="btn" href="/docs">Swagger UI (/docs)</a>
        <a class="btn" href="/redoc">ReDoc (/redoc)</a>
        <a class="btn" href="/api/v1/openapi.json">OpenAPI Schema</a>
      </div>
    </section>

    <section class="section">
      <h2>Project Team — Syntax Squad</h2>
      <div class="grid">
        {team_cards}
      </div>
    </section>

    <section class="section">
      <h2>Available API Endpoints ({len(rows)})</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Method</th>
              <th>Path</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows)}
          </tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""
    return HTMLResponse(content=page, media_type="text/html; charset=utf-8")
