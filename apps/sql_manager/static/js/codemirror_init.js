document.addEventListener('DOMContentLoaded', function () {
    var textareas = document.querySelectorAll('.codemirror-textarea');
    textareas.forEach(function (textarea) {
        var editor = CodeMirror.fromTextArea(textarea, {
            mode: 'text/x-sql',
            lineNumbers: true,
            matchBrackets: true,
            indentWithTabs: true,
            smartIndent: true,
            lineWrapping: true,
            theme: 'default'
        });
    });
});
