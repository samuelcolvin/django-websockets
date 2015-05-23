
function WebSocketConnection(){
  if (!('WebSocket' in window)) {
    alert('WebSockets are not supported by your browser.');
    return;
  }

  var url = djws.ws_url;
  log('connecting to "' + url + '" with token "' + djws.token + '"...');
  var ws = new WebSocket(url, djws.token);

  ws.onopen = function(){
    log('connected');
    ws.send('sending message on websocket opening');
  };

  ws.onmessage = function (evt) {
    log('received: ' + evt.data);
  };

  ws.onclose = function (evt) {
    log('Connection closed, reason: "' + evt.reason + '"');
    console.log('close event:', evt);
  };

  $('#user-input').submit(function (e){
    e.preventDefault();
    var msg = $('#message-box').val();
    log('sending: '+ msg);
    ws.send(msg);
  });
}

var $console = $('#console');

function log(message){
  $console.append(message + '\n');
  console.log(message)
}

$(document).ready(function(){WebSocketConnection()});
