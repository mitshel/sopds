function showHide(content_id)
{
    var content = document.getElementById(content_id);
    
    
    if (!content)
        return;

    if (content.style.display == "none")
    {
        content.style.display="block";
        
        var btn = document.getElementById(content_id + "_downbtn");
        if (btn)
            btn.style.display="none";

        var btn = document.getElementById(content_id + "_upbtn");
        if (btn)
            btn.style.display="inline";
    }
    else
    {
        content.style.display="none";
        
        var btn = document.getElementById(content_id + "_upbtn");
        if (btn)
            btn.style.display="none";

        var btn = document.getElementById(content_id + "_downbtn");
        if (btn)
            btn.style.display="inline";
    }
}