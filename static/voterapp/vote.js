"use strict";

$(document).ready(function(){

    $(".candidate-input").autocomplete({
        source: candidates
    }).on("input", function(){
        var index = $(this).data("index");
        if(index == numCandidates && index < maxCandidates){
            var button = $("#addCandidateButton");
            if($(this).val() != ""){
                button.removeClass("disabled").removeAttr("disabled");
                $("#submitBallotButton").removeClass("disabled").removeAttr("disabled");
            }else{
                button.addClass("disabled").attr("disabled", true);
                if(numCandidates == 1){
                    $("#submitBallotButton").addClass("disabled").attr("disabled", true);
                }
            }
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

    var chosenCandidates = [];

    $("#submitBallotButton").click(function(){
        var candidateList = $("#candidateList");
        var num = 1;
        chosenCandidates = [];
        for(var i = 1; i <= numCandidates; i++){
            var candidate = $("#candidateBox" + i).val();
            if(candidate != '') {
                candidateList.append($(
                    '<li class="list-group-item"><strong>' + num + '.</strong> ' + candidate + '</li>'
                ));
                chosenCandidates.push(candidate);
                num++;
            }
        }
    });

    $("#confirmVoteButton").click(function(){
        var email = $("#emailBox").val();
        // How does this work? Who knows!
        // Ask the good folks at https://stackoverflow.com/questions/46155/validate-email-address-in-javascript
        var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        if(re.test(email)){
            $("#candidatesHiddenInput").val(JSON.stringify(chosenCandidates));
            $("#submitVoteForm").submit();
        }
    })

});
