/**
 * Created by ihor on 29.11.14.
 */
document.title = "This is the new page title.";
var ws;
function onLoad() {
    ws = new WebSocket("ws://localhost:8080/websocket");
    ws.onmessage = function(e) {
        alert(e.data);
    };
}
function sendMsg() {
    ws.send(document.getElementById('msg').value);
}
//<body onload="onLoad();">
//    <strong>Message to Send:</strong>&nbsp;<input type="text" id="msg" maxlength="25" />
//    &nbsp;<input type="button" onclick="sendMsg();" value="Send" />
//</body>

//<link rel="icon" href="//i.localhost/favicon.png">
