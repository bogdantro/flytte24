function faqFunc1(){
    const answer = document.getElementById('answer1');
    const ask = document.getElementById('ask1');
    const faqPlus = document.getElementById('faqPlus1');
    const faqMinus = document.getElementById('faqMinus1');
    if (window.getComputedStyle(answer,null).getPropertyValue("opacity") == '0'){
        answer.classList.add('active');
        ask.style.borderBottom = '1px solid transparent';
        faqPlus.style.display = 'none';
        faqMinus.style.display = 'block';
    }else{
        answer.classList.remove('active');
        ask.style.borderBottom = '1px solid lightgray';
        faqPlus.style.display = 'block';
        faqMinus.style.display = 'none';
    }
}

function faqFunc2(){
    const answer = document.getElementById('answer2');
    const ask = document.getElementById('ask2');
    const faqPlus = document.getElementById('faqPlus2');
    const faqMinus = document.getElementById('faqMinus2');
    if (window.getComputedStyle(answer,null).getPropertyValue("opacity") == '0'){
        answer.classList.add('active');
        ask.style.borderBottom = '1px solid transparent';
        faqPlus.style.display = 'none';
        faqMinus.style.display = 'block';
    }else{
        answer.classList.remove('active');
        ask.style.borderBottom = '1px solid lightgray';
        faqPlus.style.display = 'block';
        faqMinus.style.display = 'none';
    }
}

function faqFunc3(){
    const answer = document.getElementById('answer3');
    const ask = document.getElementById('ask3');
    const faqPlus = document.getElementById('faqPlus3');
    const faqMinus = document.getElementById('faqMinus3');
    if (window.getComputedStyle(answer,null).getPropertyValue("opacity") == '0'){
        answer.classList.add('active');
        ask.style.borderBottom = '1px solid transparent';
        faqPlus.style.display = 'none';
        faqMinus.style.display = 'block';
    }else{
        answer.classList.remove('active');
        ask.style.borderBottom = '1px solid lightgray';
        faqPlus.style.display = 'block';
        faqMinus.style.display = 'none';
    }
}






