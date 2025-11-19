//elimiar este script , ya no fuinciona pa
document.getElementById("enviarBtn").addEventListener("click", enviarMensaje);
document.getElementById("inputTexto").addEventListener("keypress", function(e) {
  if (e.key === "Enter") enviarMensaje();
});

function enviarMensaje() {
  const input = document.getElementById("inputTexto");
  const texto = input.value.trim();
  if (texto !== "") {
    agregarMensaje("user", texto);
    responder(texto);
    input.value = "";
  }
}

function agregarMensaje(tipo, texto) {
  const messagesDiv = document.getElementById("messages");
  const msg = document.createElement("div");
  msg.className = "message " + tipo;
  msg.innerText = texto;
  messagesDiv.appendChild(msg);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function responder(textoUsuario) {
  let respuesta = "";
  if (textoUsuario.toLowerCase().includes("hola")) {
    respuesta = "¡Hola! ¿Cómo puedo ayudarte?";
  } else if (textoUsuario.toLowerCase().includes("ayuda")) {
    respuesta = "Por supuesto, dime qué quieres saber";
  }  else if (textoUsuario.toLowerCase().includes("Como estas")) {
    respuesta = "Yo me encuentro muy bien 😁";
  } else if (textoUsuario.toLowerCase().includes("gracias")) {
    respuesta = "No hay de qué :)";
  }  else if (textoUsuario.toLowerCase().includes("puedes darme informacion acerca de documentacion")) {
    respuesta = "Estoy trabajando para poder ofrecerte esa funcion 🫡";
  }  else if (textoUsuario.toLowerCase().includes("Que puedes ofrecerme")) {
    respuesta = "nada :)";
  } else {
    respuesta = "Lo siento, no entendí eso.";
  }
  setTimeout(() => agregarMensaje("bot", respuesta), 500);
}
