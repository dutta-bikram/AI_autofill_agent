"""Built-in realistic test forms for testing and demoing the AI Autofill Agent.
Includes a complex multi-section job application form and registration forms.
"""

JOB_APPLICATION_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Apex Global AI - Senior Engineer Application</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 40px 20px;
      line-height: 1.5;
    }
    .container {
      max-width: 820px;
      margin: 0 auto;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }
    .header {
      margin-bottom: 30px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
    }
    .header h1 { font-size: 26px; color: #fff; margin-bottom: 8px; }
    .header p { color: var(--text-muted); font-size: 14px; }
    .badge {
      display: inline-block;
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 12px;
    }
    .section-title {
      font-size: 18px;
      font-weight: 600;
      color: #38bdf8;
      margin: 28px 0 16px 0;
      border-bottom: 1px dashed var(--border);
      padding-bottom: 6px;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 6px;
      color: #e2e8f0;
    }
    .required { color: #f43f5e; margin-left: 2px; }
    input[type="text"], input[type="email"], input[type="tel"], input[type="url"], select, textarea {
      width: 100%;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 14px;
      color: #fff;
      font-family: inherit;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
    }
    textarea { resize: vertical; min-height: 90px; }
    .radio-group, .checkbox-group {
      display: flex;
      gap: 20px;
      margin-top: 6px;
    }
    .radio-label, .checkbox-label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-size: 14px;
      color: #cbd5e1;
    }
    .help-text {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .btn-submit {
      width: 100%;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 14px 20px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 20px;
      transition: background 0.2s, transform 0.1s;
    }
    .btn-submit:hover {
      background: var(--accent-hover);
    }
    .btn-submit:active {
      transform: scale(0.99);
    }
    #submitted-alert {
      display: none;
      background: #064e3b;
      border: 1px solid #059669;
      color: #a7f3d0;
      padding: 20px;
      border-radius: 8px;
      margin-top: 24px;
      text-align: center;
      font-size: 16px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">Live Test Form</span>
      <h1>Senior AI & Systems Automation Engineer</h1>
      <p>Apex Global AI Technologies &bull; San Francisco, CA (or Remote) &bull; Full-time</p>
    </div>

    <form id="job-app-form" onsubmit="event.preventDefault(); handleSubmit();">
      <!-- 1. Personal Info -->
      <div class="section-title">1. Candidate Information</div>
      <div class="grid-2">
        <div class="form-group">
          <label for="first_name">First Name <span class="required">*</span></label>
          <input type="text" id="first_name" name="first_name" placeholder="e.g. Alex" required>
        </div>
        <div class="form-group">
          <label for="last_name">Last Name <span class="required">*</span></label>
          <input type="text" id="last_name" name="last_name" placeholder="e.g. Rivera" required>
        </div>
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label for="email">Email Address <span class="required">*</span></label>
          <input type="email" id="email" name="email" placeholder="alex@example.com" required>
        </div>
        <div class="form-group">
          <label for="phone">Phone Number <span class="required">*</span></label>
          <input type="tel" id="phone" name="phone" placeholder="+1 (555) 000-0000" required>
        </div>
      </div>

      <div class="form-group">
        <label for="address">Street Address</label>
        <input type="text" id="address" name="address" placeholder="123 Innovation Way">
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label for="city">City</label>
          <input type="text" id="city" name="city" placeholder="San Francisco">
        </div>
        <div class="form-group">
          <label for="postal_code">Postal / Zip Code</label>
          <input type="text" id="postal_code" name="postal_code" placeholder="94107">
        </div>
      </div>

      <!-- 2. Web Links -->
      <div class="section-title">2. Professional Profiles & Links</div>
      <div class="grid-2">
        <div class="form-group">
          <label for="linkedin_url">LinkedIn Profile URL</label>
          <input type="url" id="linkedin_url" name="linkedin_url" placeholder="https://linkedin.com/in/username">
        </div>
        <div class="form-group">
          <label for="github_url">GitHub URL</label>
          <input type="url" id="github_url" name="github_url" placeholder="https://github.com/username">
        </div>
      </div>
      <div class="form-group">
        <label for="portfolio_url">Portfolio or Personal Website</label>
        <input type="url" id="portfolio_url" name="portfolio_url" placeholder="https://myportfolio.dev">
      </div>

      <!-- 3. Work Authorization & Status -->
      <div class="section-title">3. Eligibility & Preferences</div>
      <div class="form-group">
        <label>Are you legally authorized to work in the United States? <span class="required">*</span></label>
        <div class="radio-group">
          <label class="radio-label"><input type="radio" name="work_auth_us" value="Yes" required> Yes</label>
          <label class="radio-label"><input type="radio" name="work_auth_us" value="No"> No</label>
        </div>
      </div>

      <div class="form-group">
        <label>Will you now or in the future require visa sponsorship? <span class="required">*</span></label>
        <div class="radio-group">
          <label class="radio-label"><input type="radio" name="visa_sponsorship" value="No" required> No</label>
          <label class="radio-label"><input type="radio" name="visa_sponsorship" value="Yes"> Yes</label>
        </div>
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label for="notice_period">Notice Period / Availability</label>
          <select id="notice_period" name="notice_period">
            <option value="">Select notice period...</option>
            <option value="Immediately">Available Immediately</option>
            <option value="2 weeks">2 weeks</option>
            <option value="1 month">1 month</option>
            <option value="2+ months">2+ months</option>
          </select>
        </div>
        <div class="form-group">
          <label for="desired_salary">Desired Annual Compensation</label>
          <input type="text" id="desired_salary" name="desired_salary" placeholder="e.g. $145,000 USD">
        </div>
      </div>

      <div class="form-group">
        <label for="years_experience">Total Years of Professional Software Experience</label>
        <select id="years_experience" name="years_experience">
          <option value="">Select experience level...</option>
          <option value="0-1 years">0-1 years</option>
          <option value="1-3 years">1-3 years</option>
          <option value="4+ years">4+ years</option>
          <option value="7+ years">7+ years</option>
        </select>
      </div>

      <!-- 4. Qualitative RAG Questions -->
      <div class="section-title">4. Technical Deep-Dive & Qualitative Questions (RAG Powered)</div>
      
      <div class="form-group">
        <label for="challenge_question">Describe a challenging technical obstacle you overcame and how you approached it (STAR method) <span class="required">*</span></label>
        <textarea id="challenge_question" name="challenge_question" rows="4" placeholder="Detail the situation, task, actions taken, and measurable results..." required></textarea>
        <div class="help-text">Our AI RAG memory will pull your STAR stories to draft this response.</div>
      </div>

      <div class="form-group">
        <label for="why_company">Why do you want to join Apex Global AI? <span class="required">*</span></label>
        <textarea id="why_company" name="why_company" rows="3" placeholder="Share why you are excited about this mission..." required></textarea>
      </div>

      <div class="form-group">
        <label for="distributed_systems">Explain your experience with distributed systems and microservices</label>
        <textarea id="distributed_systems" name="distributed_systems" rows="3" placeholder="Discuss architecture, technologies, and scale..."></textarea>
      </div>

      <!-- 5. Verification Checkbox -->
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="terms_agree" name="terms_agree" required>
          <span>I certify that all statements in this application are true and complete. <span class="required">*</span></span>
        </label>
      </div>

      <button type="submit" id="submit-btn" class="btn-submit">Submit Application</button>
    </form>

    <div id="submitted-alert">
      <h3>🎉 Application Successfully Submitted!</h3>
      <p style="margin-top: 8px;">All form fields have been validated and recorded by the AI Autofill Agent.</p>
    </div>
  </div>

  <script>
    function handleSubmit() {
      document.getElementById('job-app-form').style.opacity = '0.4';
      document.getElementById('submit-btn').disabled = true;
      document.getElementById('submitted-alert').style.display = 'block';
      document.getElementById('submitted-alert').scrollIntoView({ behavior: 'smooth' });
    }
  </script>
</body>
</html>
"""
