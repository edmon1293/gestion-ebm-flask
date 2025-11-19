(function(){
  const form = document.getElementById('registerForm');
  const pw = document.getElementById('password');
  const pwBar = document.getElementById('pwBar');
  const pwLabel = document.getElementById('pwLabel');
  const toggle = document.getElementById('togglePw');
  const resetBtn = document.getElementById('resetBtn');
  const username = document.getElementById('username');
  const usernameErr = document.getElementById('usernameErr');
  const formError = document.getElementById('formError');

  function scorePassword(p){
    let score = 0;
    if(!p) return 0;
    if(p.length >= 8) score += 1;
    if(p.match(/[a-z]/)) score += 1;
    if(p.match(/[A-Z]/)) score += 1;
    if(p.match(/[0-9]/)) score += 1;
    if(p.match(/[^A-Za-z0-9]/)) score += 1;
    return score;
  }

  function updatePwMeter(){
    const s = scorePassword(pw.value);
    const percent = (s/5)*100;
    pwBar.style.width = percent + '%';
    pwBar.className = '';
    if(s <= 2){ pwBar.classList.add('pw-weak'); pwLabel.textContent = 'Débil'; }
    else if(s === 3 || s === 4){ pwBar.classList.add('pw-medium'); pwLabel.textContent = 'Mediana'; }
    else { pwBar.classList.add('pw-strong'); pwLabel.textContent = 'Fuerte'; }
  }

  pw.addEventListener('input', updatePwMeter);

  toggle.addEventListener('click', ()=>{
    if(pw.type === 'password'){ pw.type = 'text'; toggle.textContent = 'Ocultar'; }
    else { pw.type = 'password'; toggle.textContent = 'Mostrar'; }
  });

  resetBtn.addEventListener('click', ()=>{
    form.reset();
    pwBar.style.width = '0%';
    pwLabel.textContent = '';
    usernameErr.style.display = 'none';
    formError.style.display = 'none';
  });

  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    usernameErr.style.display = 'none';
    formError.style.display = 'none';

    const u = username.value.trim();
    const password = pw.value;
    const area = document.getElementById('area').value;
    const nivel = document.getElementById('nivel').value;

    if(u.length < 3){ usernameErr.style.display = 'block'; return; }
    if(password.length < 8){ formError.textContent = 'La contraseña debe tener al menos 8 caracteres.'; formError.style.display='block'; return; }
    if(!area){ formError.textContent = 'Selecciona un área.'; formError.style.display='block'; return; }
    if(!nivel){ formError.textContent = 'Selecciona un nivel.'; formError.style.display='block'; return; }

    const payload = { username:u, password:password, area:area, nivel:nivel };
    
    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if(response.ok){
        alert('Usuario "' + u + '" creado correctamente');
        form.reset();
        pwBar.style.width='0%';
        pwLabel.textContent='';
      } else {
        const data = await response.json();
        formError.textContent = data.error || 'Error al crear usuario.';
        formError.style.display = 'block';
      }
    } catch(err){
      formError.textContent = 'Error de conexión al servidor.';
      formError.style.display = 'block';
      console.error(err);
    }
  });
})();
