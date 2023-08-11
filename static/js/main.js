async function onPageLoadFunc(){
    setTimeout(() => {
        document.getElementById('onPageLoad').classList.add('hide');
    }, 500);
}
setInterval(() => {
    onPageLoadFunc();
}, 100);
