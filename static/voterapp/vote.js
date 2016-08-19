"use strict";

var chosenCandidates = [];

$(document).ready(function(){

    $(".candidate-input").autocomplete({
        source: Object.keys(candidates)
    }).on("input", function(){
        var index = $(this).data("index");
        if(index == numCandidates && index < maxCandidates){
            var button = $("#addCandidateButton");
            if($(this).val() != ""){
                button.removeClass("disabled").removeAttr("disabled");
                $("#submitBallotButton").removeClass("disabled").removeAttr("disabled");
            }else{
                //button.addClass("disabled").attr("disabled", true);
                if(numCandidates == 1){
                    $("#submitBallotButton").addClass("disabled").attr("disabled", true);
                }
            }
        }
    }).change(function(){
        var textBox = $(this);
        var input = toTitleCase(textBox.val());
        textBox.val(input);
        if(!candidates.hasOwnProperty(input)){
            var guesses = [];
            for(var candidate in candidates){
                if(candidates.hasOwnProperty(candidate) && getEditDistance(candidate, input) <= 4){
                    guesses.push(candidate);
                }
            }
            console.log(guesses);
        }
    });

    var numCandidates = 1;
    $("#addCandidateButton").click(function(){
        console.log("NumCandidates: " + numCandidates);
        if(numCandidates < maxCandidates){
            numCandidates++;
            $(".remove-candidate-button").removeClass("hidden");
            $("#candidateDiv" + numCandidates).removeClass("hidden");
            if(numCandidates == maxCandidates) {
                $("#addCandidateButton").addClass("disabled").attr("disabled", true);
            }
        }
    });

    $(".remove-candidate-button").click(function(){
        console.log("Click!");
        if(numCandidates > 1){
            var i = $(this).data("index");
            //var i = index;
            var currentInput = $("#candidateBox" + i);
            i++;
            var nextInput = $("#candidateBox" + i);
            while(nextInput && !nextInput.parent("div.candidate-div").hasClass("hidden") && i <= maxCandidates){
                console.log("Current: " + i);
                currentInput.val(nextInput.val());
                currentInput = nextInput;
                i++;
                nextInput = $("#candidateBox" + i);
            }
            currentInput.val("");
            currentInput.parent("div.candidate-div").addClass("hidden");
            numCandidates--;
            if(numCandidates == 1){
                $(".remove-candidate-button").addClass("hidden");
            }
        }
    });

    //var chosenCandidates = [];

    $("#submitBallotButton").click(function(){
        var candidateList = $("#candidateList");
        var num = 1;
        chosenCandidates = [];
        candidateList.children().remove();
        for(var i = 1; i <= numCandidates; i++){
            var candidate = $("#candidateBox" + i).val();
            if(candidate != '' && chosenCandidates.indexOf(candidate) < 0) {
                candidateList.append($(
                    '<li class="list-group-item"><strong>' + num + '.</strong> ' + candidate + '</li>'
                ));
                chosenCandidates.push({
                    'name': candidate,
                    'id': candidates[candidate]
                });
                num++;
            }
        }
    });

    $("#submitVoteModal").on("shown.bs.modal", function(){
        console.log("Modal shown");
        $("#normalVoteBox").autocomplete({
            source: Object.keys(candidates),
            appendTo: '#submitVoteModal'
        });
    });

    $("#confirmVoteButton").click(function(){
        if(submitForm()){
            $("#submitVoteForm").submit();
        }
    });

    $("#emailBox").keypress(function(event){
        if(event.which == 13 && !submitForm()){
            event.preventDefault();
        }
    });

    $('[data-toggle="popover"]').popover();
});

function submitForm(){
    console.log("Submitted")
    var email = $("#emailBox").val();
    // How does this work? Who knows!
    // Ask the good folks at https://stackoverflow.com/questions/46155/validate-email-address-in-javascript
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    if(re.test(email)){
        $("#candidatesHiddenInput").val(JSON.stringify(chosenCandidates));
        var normalVoteName = $("#normalVoteBox").val();
        if(normalVoteName && normalVoteName != "") {
            $("#normalVoteHiddenInput").val(JSON.stringify({
                'name': normalVoteName,
                'id': candidates[normalVoteName]
            }));
        }else{
            $("#normalVoteHiddenInput").val("{}");
        }
        return true;
    }else{
        $("#submitVoteForm").children("div.form-inline").addClass("error");
        $("#emailBoxError").removeClass("hidden");
    }
}

/*
Copyright (c) 2011 Andrei Mackenzie
Source: https://gist.github.com/andrei-m/982927
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

// Compute the edit distance between the two given strings
function getEditDistance(a, b){
  if(a.length == 0) return b.length;
  if(b.length == 0) return a.length;

  var matrix = [];

  // increment along the first column of each row
  var i;
  for(i = 0; i <= b.length; i++){
    matrix[i] = [i];
  }

  // increment each column in the first row
  var j;
  for(j = 0; j <= a.length; j++){
    matrix[0][j] = j;
  }

  // Fill in the rest of the matrix
  for(i = 1; i <= b.length; i++){
    for(j = 1; j <= a.length; j++){
      if(b.charAt(i-1) == a.charAt(j-1)){
        matrix[i][j] = matrix[i-1][j-1];
      } else {
        matrix[i][j] = Math.min(matrix[i-1][j-1] + 1, // substitution
                                Math.min(matrix[i][j-1] + 1, // insertion
                                         matrix[i-1][j] + 1)); // deletion
      }
    }
  }

  return matrix[b.length][a.length];
}

/*
Source: https://stackoverflow.com/questions/196972/convert-string-to-title-case-with-javascript
 */
function toTitleCase(str){
    return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
}
