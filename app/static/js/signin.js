/* static/js/signin.js
 */

function toggle_hiw(){
    var landing_content = document.getElementById('landing-content');
    var hiw_content= document.getElementById('how-it-works-content');

    if(!landing_content.getAttribute('hidden')){
        // Landing content is not hidden
        landing_content.setAttribute('hidden', 'true');
        hiw_content.removeAttribute('hidden');
    }else{
        // Landing content is hidden
        landing_content.removeAttribute('hidden');
        hiw_content.setAttribute('hidden', 'true')
    }
}
