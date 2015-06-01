$(document).ready(function(){
  if (!('WebSocket' in window)) {
    alert('WebSockets are not supported by your browser.');
    return;
  }

  var ws = null;

  function close(){
    log('closing connection...');
    ws.close();
    ws = null;
  }
  $('#close').click(close);

  function open(){
    if (ws !== null){
      close();
    }
    var url = djws.ws_url;
    log('connecting to "' + url + '" with token "' + djws.token + '"...');
    ws = new WebSocket(url, djws.token);

    ws.onopen = function(){
      log('connected');
    };

    ws.onmessage = function (evt) {
      log('< ' + evt.data);
    };

    ws.onclose = function (evt) {
      log('Connection closed, reason: "' + evt.reason + '", code: ' + evt.code);
      console.log('close event:', evt);
    };
  }
  $('#open').click(open);
  open();

  $('#user-input').submit(function (e){
    e.preventDefault();
    var msg = $msg_box.val();
    log('> '+ msg);
    ws.send(msg);
    $msg_box.val('');
  });
});

var $console = $('#console');
var $msg_box = $('#message-box');

function log(message){
  $console.append(message + '\n');
  console.log(message);
  $console[0].scrollTop = $console.height();
}
