prototype = """
<div class="search-result" data-pkg="LIBRARYNAME">
    <b>LIBRARYORDER. LIBRARYNAME <span class="star" onclick="toggleStar('LIBRARYNAME')">☆</span></b>
    <div class="meta">LIBRARYMETADATA</div>
    <div class="description">LIBRARYDESCRIPTION</div>
    <div class="actions">
        <a href="LIBRARYLINK" target="_blank" rel="noopener" class="action-btn">🔗 PyPI</a>
        <a href="LIBRARYHOME" target="_blank" rel="noopener" class="action-btn">🏠 Home</a>
    </div>
</div>
"""

progress_bar = """
<div class="progress-alert">
  <span class="message">MESSAGE</span>
  <span class="percent">PROGRESSNOW</span>
</div>
"""

old_request = """
<div class="error-alert">
  ⚠️ Request no longer valid (e.g. due to server restart).
</div>
"""

register_page = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Register – FLARE</title></head>
<body style="background:#111;color:#fff;font-family:Segoe UI,Roboto,sans-serif;
             display:flex;justify-content:center;align-items:center;height:100vh;">
  <form method="post" style="background:#1c1c1c;padding:2rem;border-radius:10px;
                              box-shadow:0 3px 8px rgba(0,0,0,0.4);min-width:300px;">
    <h2 style="margin-top:0;">Register</h2>
    <input name="username" placeholder="Username"
           style="width:100%;margin:.5rem 0;padding:.5rem;border:1px solid #333;
                  border-radius:8px;background:#000;color:#fff;">
    <input type="password" name="password" placeholder="Password"
           style="width:100%;margin:.5rem 0;padding:.5rem;border:1px solid #333;
                  border-radius:8px;background:#000;color:#fff;">
    <button type="submit"
            style="margin-top:1rem;width:100%;padding:.6rem;background:#fff;color:#000;
                   font-weight:600;border:none;border-radius:8px;cursor:pointer;">
      Create Account
    </button>
  </form>
</body>
</html>
"""

login_page = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Login – FLARE</title></head>
<body style="background:#111;color:#fff;font-family:Segoe UI,Roboto,sans-serif;
             display:flex;justify-content:center;align-items:center;height:100vh;">
  <form method="post" style="background:#1c1c1c;padding:2rem;border-radius:10px;
                              box-shadow:0 3px 8px rgba(0,0,0,0.4);min-width:300px;">
    <h2 style="margin-top:0;">Login</h2>
    <input name="username" placeholder="Username"
           style="width:100%;margin:.5rem 0;padding:.5rem;border:1px solid #333;
                  border-radius:8px;background:#000;color:#fff;">
    <input type="password" name="password" placeholder="Password"
           style="width:100%;margin:.5rem 0;padding:.5rem;border:1px solid #333;
                  border-radius:8px;background:#000;color:#fff;">
    <button type="submit"
            style="margin-top:1rem;width:100%;padding:.6rem;background:#fff;color:#000;
                   font-weight:600;border:none;border-radius:8px;cursor:pointer;">
      Sign In
    </button>
  </form>
</body>
</html>
"""