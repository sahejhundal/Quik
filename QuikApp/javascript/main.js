$(function(){
  $('.chips-placeholder').material_chip({
      placeholder: '',
      secondaryPlaceholder: 'Who to?',
      name: 'to',
  });
});

$(document).ready(function(){
    var element = document.getElementById("section");
    element.scrollTop = element.scrollHeight;
});



function deletePost(postid){
  $.ajax('/delete-post', {
    type: 'POST',
    data: {
      postid: postid
    }
  });
}
/*function showPostSettings(postid){
  $.ajax('/find', {
    type: 'GET',
    data: {
      postid: postid
    }
  });
}*/

function Text(text, chat_id, to){
  console.log('Post request recieved');
  if(text.val()===""){
    console.log("Went into this")
    event.preventDefault()
    return false;
  }
  $(".overlay").show();
  $.ajax('/chat/' + to, {
    type: 'POST',
    data: {
      text: text.val(),
      chat_id: chat_id
    },
    success: function(){
      $(".overlay").hide();
      console.log("Done!")
    }
  });
  event.preventDefault();
  return false;
}
/*onClick="this.setSelectionRange(0, this.value.length)"*/
