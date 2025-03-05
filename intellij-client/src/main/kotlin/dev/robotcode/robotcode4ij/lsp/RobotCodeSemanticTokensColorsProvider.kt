package dev.robotcode.robotcode4ij.lsp

import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.psi.PsiFile
import com.redhat.devtools.lsp4ij.features.semanticTokens.DefaultSemanticTokensColorsProvider
import com.redhat.devtools.lsp4ij.features.semanticTokens.SemanticTokensColorsProvider
import dev.robotcode.robotcode4ij.highlighting.Colors

private val mapping by lazy {
    mapOf(
        "header" to Colors.HEADER,
        "headerKeyword" to Colors.HEADER,
        "headerComment" to Colors.HEADER,
        "headerSettings" to Colors.HEADER,
        "headerVariable" to Colors.HEADER,
        "headerTestcase" to Colors.HEADER,
        "headerTask" to Colors.HEADER,
        
        "setting" to Colors.SETTING,
        "settingImport" to Colors.SETTING_IMPORT,
        "controlFlow" to Colors.CONTROL_FLOW,
        
        "testcaseName" to Colors.TESTCASE_NAME,
        "keywordName" to Colors.KEYWORD_NAME,
        "keywordCall" to Colors.KEYWORD_CALL,
        "keywordCallInner" to Colors.KEYWORD_CALL_INNER,
        "nameCall" to Colors.NAME_CALL,
        "argument" to Colors.ARGUMENT,
        "embeddedArgument" to Colors.EMBEDDED_ARGUMENT,
        "namedArgument" to Colors.NAMED_ARGUMENT,
        "variable" to Colors.VARIABLE,
        "variableExpression" to Colors.VARIABLE_EXPRESSION,
        "variableBegin" to Colors.VARIABLE_BEGIN,
        "variableEnd" to Colors.VARIABLE_END,
        
        "namespace" to Colors.NAMESPACE,
        "bddPrefix" to Colors.BDD_PREFIX,
        "continuation" to Colors.CONTINUATION
    )
}

class RobotCodeSemanticTokensColorsProvider : DefaultSemanticTokensColorsProvider() {
    override fun getTextAttributesKey(
        tokenType: String, tokenModifiers: MutableList<String>, file: PsiFile
    ): TextAttributesKey? {
        val result = mapping[tokenType] ?: super.getTextAttributesKey(tokenType, tokenModifiers, file)
        
        return result ?: run {
            thisLogger().warn("Unknown token type: $tokenType")
            null
        }
    }
}

