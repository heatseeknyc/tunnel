$(function() {
  var maxChars = 4;
  var allowedChars = new RegExp("^[a-zA-Z0-9]+$");
  var forbiddenChars = new RegExp("[^a-zA-Z0-9]", 'g');
  var submitBtn = $("#getStarted");
  var inputField = $('#xbeeId');

  inputField.keypress(function(event) {
    limitLength(this, event);
    limitCharacters(event);
    enableButton(this);
  }).keyup(function(event) {
    limitLength(this, event);
    limitCopyPasteCharacters(this);
    enableButton(this);
  });

  function enableButton(element) {
    var disabled = inputField.val().length === maxChars ? false : true;
    submitBtn.prop('disabled', disabled);
  }

  function limitCharacters(e) {
    var str = String.fromCharCode(!e.charCode ? e.which : e.charCode);
    if (allowedChars.test(str)) {
        return true;
    }
    e.preventDefault();
    return false;
  }

  function limitCopyPasteCharacters(element) {
    if (forbiddenChars.test($(element).val())) {
      $(element).val($(element).val().replace(forbiddenChars, ''));
    }
  }

  function limitLength(element, event) {
    if ($(element).val().length >= maxChars) {
      event.preventDefault();
      $(element).val($(element).val().substr(0, maxChars));
    }
  }

  $('#form').submit(function(event) {
    event.preventDefault();
    location = '/' + $('#xbeeId').val().toLowerCase().replace('o', '0');
  });

});
