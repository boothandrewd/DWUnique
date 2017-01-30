/* app/static/js/dashboard.js
 */

function updateIFrame(iFrame){
    iFrame.width = $(iFrame).parent().width();
    iFrame.height = $(iFrame).parent().height();
}

function updateIFrames(){
    var iFrames = $('iframe');
    for(var counter = 0; counter < iFrames.length; counter++){
        updateIFrame(iFrames[counter]);
    }
}

$(window).resize(updateIFrames);

function switch_content(elem){
    var content_name = elem.getAttribute('data-sidebar-name');
    console.log(content_name);

    $('.content-li').removeClass('active');
    $('.content-div').hide();

    $("[data-sidebar-name='" + content_name + "']").addClass('active');
    $('#' + content_name).show();
}

function hide_content(){
    $('.content-div').hide();
    $('#dwu').show();
}

$(function(){
    updateIFrames();
    hide_content();
});

