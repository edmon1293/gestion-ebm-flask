document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("mensaje");
  const enviarBtn = document.getElementById("enviar-btn");
  const chatBox = document.getElementById("chat-box");
  const historialList = document.getElementById("historial-conversaciones");
  const nuevoChatBtn = document.getElementById("nuevo-chat-btn");
  const USERNAME = document.body.dataset.username; 




  let historialActivo = null;

  // =========================
  // FUNCIONES DE INTERFAZ
  // =========================
  function mostrarMensajeUsuario(texto) {
    const div = document.createElement("div");
    div.className = "mensaje usuario";
    div.textContent = texto;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function mostrarRespuesta(texto) {
    const div = document.createElement("div");
    div.className = "mensaje bot";
    div.textContent = texto;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function mostrarCargando() {
    const div = document.createElement("div");
    div.className = "mensaje bot cargando";
    div.textContent = "Pensando...";
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
  }

  function eliminarHistorial(id) {
    if (!confirm("¿Eliminar esta conversación?")) return;

    fetch(`/eliminar_historial/${id}`, { method: "DELETE" })
        .then(res => {
            if (res.ok) {
                cargarHistorial(); // Recargar lista
                document.getElementById("chat-box").innerHTML = `
                    <div class="mensaje bot">Conversación eliminada ✅</div>
                `;
            }
        })
        .catch(err => console.log("Error al eliminar historial:", err));
}


  // =========================
  // FUNCIONES DE CHAT
  // =========================
  async function enviarMensaje(mensaje) {
    const cargandoDiv = mostrarCargando();
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje })
      });

      chatBox.removeChild(cargandoDiv);

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        mostrarRespuesta(data.error || `⚠️ Error del servidor: ${res.status}`);
        return;
      }

      const data = await res.json();
      mostrarRespuesta(data.respuesta);
      cargarTitulosHistorial();
    } catch (error) {
      chatBox.removeChild(cargandoDiv);
      mostrarRespuesta("⚠️ Error al conectar con el servidor.");
      console.error(error);
    }
  }

  async function cargarTitulosHistorial() {
    try {
      const res = await fetch("/historial_titulos");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      historialList.innerHTML = "";
      data.forEach(h => {
        const li = document.createElement("li");
        li.textContent = `${h.titulo} (${h.fecha})`;
        li.dataset.id = h.id;
        li.addEventListener("click", async () => {
  // Marca este historial como el activo en sesión
  await fetch(`/set_historial_activo/${h.id}`, { method: "POST" });

  // Limpia el chat antes de cargar el historial
  chatBox.innerHTML = "";

  // Carga los mensajes del historial
  cargarHistorialDetalle(h.id);
});
        historialList.appendChild(li);
      });
    } catch (error) {
      console.error(error);
    }
  }

  async function cargarHistorialDetalle(id) {
    try {
      const res = await fetch(`/historial_detalle/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const mensajes = await res.json();

      chatBox.innerHTML = "";
      mensajes.forEach(m => {
        const div = document.createElement("div");
        div.className = `mensaje ${m.remitente}`;
        div.textContent = m.texto;
        chatBox.appendChild(div);
      });
      chatBox.scrollTop = chatBox.scrollHeight;

      historialActivo = id;
    } catch (error) {
      console.error(error);
      mostrarRespuesta("⚠️ No se pudieron cargar los mensajes.");
    }
  }

  // =========================
  // NUEVO CHAT
  // =========================
  nuevoChatBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/nuevo_chat", { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      historialActivo = data.id_historial;
      chatBox.innerHTML = "";

      mostrarRespuesta(`¡Hola ${USERNAME}! ¿Cómo puedo ayudarte hoy?`);
      cargarTitulosHistorial();
    } catch (error) {
      console.error(error);
      mostrarRespuesta("⚠️ No se pudo iniciar un nuevo chat.");
    }
  });

  // =========================
  // ENVÍO DE MENSAJES
  // =========================
  enviarBtn.addEventListener("click", () => {
    const mensaje = input.value.trim();
    if (mensaje !== "") {
      mostrarMensajeUsuario(mensaje);
      enviarMensaje(mensaje);
      input.value = "";
    }
  });

  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      enviarBtn.click();
    }
  });

  // =========================
  // INICIALIZACIÓN
  // =========================
  // Mensaje de bienvenida al cargar la página
  chatBox.innerHTML = "";
  mostrarRespuesta(`¡Hola ${USERNAME}! ¿Cómo puedo ayudarte hoy?`);
  cargarTitulosHistorial();

});
