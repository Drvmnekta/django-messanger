console.log("Sanity check from room.js.");

const roomName = JSON.parse(document.getElementById('roomName').textContent);
const currentUser = document.getElementById("currentUser").value;
const chatSocket = new WebSocket("ws://" + window.location.host + "/ws/chat/" + roomName + "/");

const chatLog = document.querySelector("#chatLog");
const chatMessageInput = document.querySelector("#chatMessageInput");
const chatMessageSend = document.querySelector("#chatMessageSend");
const allUsersSelector = document.querySelector("#allUsersSelector");
const formTyping = document.querySelector("#formTyping");
const countNotReadMessage = document.getElementById("countNotReadMessage");

let pageUp = 0;
let pageDown = 0;
let isLastUpMessage = false;
let isLastDownMessage = false;
let isTyping = false;
let timeoutId = null;


const optionsForObserver = {
  root: chatLog,
  rootMargin: '0px',
  threshold: 0.05,
}
const callbackForObserver = (entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
        if (entry.target.classList.contains('not-read')) {
            chatSocket.send(JSON.stringify({
               "type": "read_message",
               "id": entry.target.id,
            }));
        }
    }
  });
};
const observer = new IntersectionObserver(callbackForObserver, optionsForObserver);


// adds a new option to 'usersSelector'
function usersSelectorAdd(username) {
    if (document.querySelector('li[data-username="' + username + '"]')) return;
    let newLi = document.createElement("li");
    newLi.setAttribute("data-username", username);
    newLi.classList.add("mx-3");
    newLi.innerHTML = username;
    allUsersSelector.appendChild(newLi);
}

// removes an option from 'usersSelector'
function onlineUsersSelectorRemove(username) {
    let oldLi= document.querySelector('li[data-username="' + username + '"]');
    if (oldLi !== null) {
        oldLi.style.listStyleType = "none";
    }
}

// adds a new option to 'allUsersSelector'
function onlineUsersSelectorAdd(username) {
    let onlineUser = document.querySelector('li[data-username="' + username + '"]');
    if (onlineUser) {
        onlineUser.style.listStyleType = "disc";
    }
}

function addCountOfNotReadMessages(count) {
    if (!!count) {
        countNotReadMessage.textContent = count;
        document.getElementById("circleNotReadMessage").style.display = "block";
    } else {
        document.getElementById("circleNotReadMessage").style.display = "none";
    }
}

function onMessagesDownClick() {
    const count = countNotReadMessage.textContent;

    if (!!count) {
        pageDown = Math.floor(count/20);
        chatSocket.send(JSON.stringify({
               "type": "paginate_down",
               "page": pageDown,
        }));
        chatSocket.send(JSON.stringify({
               "type": "paginate_down",
               "page": pageDown + 1,
        }));
        isLastDownMessage = true;
        observer.unobserve;
        chatLog.textContent = '';
    }
}

function addNewMessage(message) {
    const div = document.createElement("div");
    div.setAttribute("id", message.message_id);
    div.classList.add("body-message");
    div.setAttribute('title', message.date);

    if (message.user === currentUser) {
        div.classList.add("right");
    }

    if (!message.read_message) {
        div.classList.add("not-read");
    }

    const divUserTime = document.createElement("div");

    const spanUser = document.createElement("span");
    spanUser.classList.add("username");
    spanUser.textContent = message.user;
    divUserTime.append(spanUser);

    const spanTime = document.createElement("span");
    spanTime.classList.add("time");
    spanTime.textContent = message.time;
    divUserTime.append(spanTime);

    div.append(divUserTime);

    const text = document.createTextNode(message.message);
    div.append(text);

    return div;
}

function addNewMessageList(messageList, directionPaginate = "down") {
    if (!!messageList?.length) {
        let fragment = document.createDocumentFragment();

        if (directionPaginate === 'up') {
            for (let i = messageList.length - 1; i >= 0; i--) {
               fragment.append(addNewMessage(messageList[i]));
            }
            chatLog.prepend(fragment);
            chatLog.scrollTop = '1';
        } else if (directionPaginate === 'down') {
            for (let i = 0; i < messageList.length; i++) {
               fragment.append(addNewMessage(messageList[i]));
            }
            chatLog.append(fragment);
        }
    }
}

function addUserTyping(message, user = null) {
    if (!message || user === currentUser) {
        formTyping.textContent = "";
        return;
    }
    formTyping.textContent = message;
}

function onInputChatMessageChange() {
    if (isTyping) {
        chatSocket.send(JSON.stringify({
            "type": "user_stop_typing",
        }));
    }
    isTyping = false;
}

function onInputChatMessageInput() {
    if (!isTyping) {
        chatSocket.send(JSON.stringify({
            "type": "user_typing",
        }));
    }

    isTyping = true;
    clearTimeout(timeoutId);

    timeoutId = setTimeout(function() {
        if (isTyping) {
            chatSocket.send(JSON.stringify({
                "type": "user_stop_typing",
            }));
        }
        isTyping = false;
    }, 2000);
}

function onChatLogScroll() {
    if (chatLog.scrollTop === 0 && !isLastUpMessage && chatLog.textContent !== '') {
        chatSocket.send(JSON.stringify({
               "type": "paginate_up",
               "page": pageUp + 1,
        }));
    } else if (chatLog.scrollHeight === chatLog.scrollTop + chatLog.clientHeight && !isLastDownMessage && chatLog.textContent !== '') {
        chatSocket.send(JSON.stringify({
               "type": "paginate_down",
               "page": pageDown + 1,
        }));
    }
}

function observeNewMessages() {
    setTimeout(() => {
        const targetList = document.querySelectorAll('.body-message');

        targetList.forEach(i => {
            observer.observe(i);
        })
    }, "2000");
}

function readMessage(id) {
    let element = document.getElementById(id.toString());
    element.classList.remove('not-read');
}

function paginate(messageList) {
    if (messageList?.length > 1) {
        for (let i = 0; i < messageList.length; i++) {
           if (!messageList[i].read_message) {
               document.getElementById(messageList[i].message_id).scrollIntoView({block: "center"});
               break;
           }
           if (i === messageList.length - 1) {
               chatLog.scrollTop = chatLog.scrollHeight;
           }
        }
    } else if (messageList?.length === 1) {
        if (messageList[0].user === currentUser) {
            chatLog.scrollTop = chatLog.scrollHeight;
        }
    }
}

// focus 'chatMessageInput' when user opens the page
chatMessageInput.focus();

// submit if the user presses the enter key
chatMessageInput.onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter key
        chatMessageSend.click();
    }
};

chatMessageInput.addEventListener("change", onInputChatMessageChange);

chatMessageInput.addEventListener("input", onInputChatMessageInput);

chatLog.addEventListener("scroll", onChatLogScroll);

// clear the 'chatMessageInput' and forward the message
chatMessageSend.onclick = function() {
    if (chatMessageInput.value.length === 0) return;
    chatSocket.send(JSON.stringify({
        "type": "chat_message",
        "message": chatMessageInput.value,
    }));
    chatMessageInput.value = "";
};

document.addEventListener("beforeunload", function() {
    chatMessageInput.removeEventListener("change", onInputChatMessageChange);
    chatMessageInput.removeEventListener("input", onInputChatMessageInput);
    chatLog.removeEventListener("scroll", onChatLogScroll);
});


function connect() {
    chatSocket.onopen = function(e) {
        console.log("Successfully connected to the WebSocket.");
    }

    chatSocket.onclose = function(e) {
        console.log("WebSocket connection closed unexpectedly. Trying to reconnect in 2s...");
        setTimeout(function() {
            console.log("Reconnecting...");
            connect();
        }, 2000);
    };

    chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log(data);

    switch (data.type) {
        case "chat_message":
            addNewMessageList(data.messages, 'down');
            addCountOfNotReadMessages(data?.count);
            paginate(data.messages);

            if (!data.messages?.length) {
               chatLog.innerHTML = "<div class=\"notification\">Нет сообщений</div>" + chatLog.innerHTML;
            }

            observeNewMessages();
            break;
        case "user_join":
            chatLog.innerHTML += "<div class=\"notification\">" + data.user + " присоединился<div>";
            usersSelectorAdd(data.user);
            break;
        case "online_users":
            for (let i = 0; i < data.users.length; i++) {
                onlineUsersSelectorAdd(data.users[i]);
            }
            break;
        case "user_leave":
            chatLog.innerHTML += "<div class=\"notification\">" + data.user + " вышел из комнаты <div>";
            onlineUsersSelectorRemove(data.user);
            break;
        case "paginate_up":
             let currentScrollHeight = chatLog.scrollHeight;
             addNewMessageList(data.messages, "up");

             if (!!data.messages?.length > 0) {
                pageUp++;
             } else {
                chatLog.innerHTML = "<div class=\"notification\">Нет сообщений</div>" + chatLog.innerHTML;
                isLastUpMessage = true;
             }

             chatLog.scrollTop = chatLog.scrollHeight - currentScrollHeight;
            break;
        case "paginate_down":
            addNewMessageList(data.messages, "down");

            if (!!data.messages?.length > 0) {
                pageDown++;
            } else {
                isLastDownMessage = true;
            }

            addCountOfNotReadMessages(data?.count);
            paginate(data.messages);

            observeNewMessages();
            break;
        case "user_typing":
            addUserTyping(data.message, data.user);
            break;
        case "user_stop_typing":
            addUserTyping(data.message);
            break;
        case "read_message":
            readMessage(data.message_id);
            break;
        default:
            console.error("Unknown message type!");
            break;
        }
    };

    chatSocket.onerror = function(err) {
        console.log("WebSocket encountered an error: " + err.message);
        console.log("Closing the socket.");
        chatSocket.close();
    }
}
connect();