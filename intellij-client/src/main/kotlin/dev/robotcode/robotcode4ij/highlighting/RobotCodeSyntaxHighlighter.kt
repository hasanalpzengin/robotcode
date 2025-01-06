package dev.robotcode.robotcode4ij.highlighting

import com.intellij.lexer.Lexer
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.fileTypes.PlainSyntaxHighlighter
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase
import com.intellij.psi.tree.IElementType
import com.intellij.util.containers.ContainerUtil
import dev.robotcode.robotcode4ij.psi.ARGUMENT
import dev.robotcode.robotcode4ij.psi.COMMENT_BLOCK
import dev.robotcode.robotcode4ij.psi.COMMENT_LINE
import dev.robotcode.robotcode4ij.psi.CONTINUATION
import dev.robotcode.robotcode4ij.psi.CONTROL_FLOW
import dev.robotcode.robotcode4ij.psi.ENVIRONMENT_VARIABLE_BEGIN
import dev.robotcode.robotcode4ij.psi.ENVIRONMENT_VARIABLE_END
import dev.robotcode.robotcode4ij.psi.HEADER
import dev.robotcode.robotcode4ij.psi.KEYWORD_CALL
import dev.robotcode.robotcode4ij.psi.KEYWORD_NAME
import dev.robotcode.robotcode4ij.psi.OPERATOR
import dev.robotcode.robotcode4ij.psi.RobotTextMateElementType
import dev.robotcode.robotcode4ij.psi.SETTING
import dev.robotcode.robotcode4ij.psi.TESTCASE_NAME
import dev.robotcode.robotcode4ij.psi.VARIABLE
import dev.robotcode.robotcode4ij.psi.VARIABLE_BEGIN
import dev.robotcode.robotcode4ij.psi.VARIABLE_END
import org.jetbrains.plugins.textmate.TextMateService
import org.jetbrains.plugins.textmate.language.TextMateScopeComparator
import org.jetbrains.plugins.textmate.language.syntax.highlighting.TextMateTheme
import org.jetbrains.plugins.textmate.language.syntax.lexer.TextMateScope
import java.util.function.Function


class RobotCodeHighlighter : SyntaxHighlighterBase() {
    companion object {
        val elementTypeMap = mapOf(
            COMMENT_LINE to arrayOf(RobotColors.LINE_COMMENT),
            COMMENT_BLOCK to arrayOf(RobotColors.BLOCK_COMMENT),
            VARIABLE_BEGIN to arrayOf(RobotColors.VARIABLE_BEGIN),
            VARIABLE_END to arrayOf(RobotColors.VARIABLE_END),
            ENVIRONMENT_VARIABLE_BEGIN to arrayOf(RobotColors.VARIABLE_BEGIN),
            ENVIRONMENT_VARIABLE_END to arrayOf(RobotColors.VARIABLE_END),
            TESTCASE_NAME to arrayOf(RobotColors.TESTCASE_NAME),
            KEYWORD_NAME to arrayOf(RobotColors.KEYWORD_NAME),
            HEADER to arrayOf(RobotColors.HEADER),
            SETTING to arrayOf(RobotColors.SETTING),
            KEYWORD_CALL to arrayOf(RobotColors.KEYWORD_CALL),
            CONTROL_FLOW to arrayOf(RobotColors.CONTROL_FLOW),
            VARIABLE to arrayOf(RobotColors.VARIABLE),
            OPERATOR to arrayOf(RobotColors.OPERATOR),
            ARGUMENT to arrayOf(RobotColors.ARGUMENT),
            CONTINUATION to arrayOf(RobotColors.CONTINUATION),
        )
        
        val PLAIN_SYNTAX_HIGHLIGHTER: PlainSyntaxHighlighter = PlainSyntaxHighlighter()
    }
    
    private val myLexer = RobotTextMateHighlightingLexer()
    
    override fun getHighlightingLexer(): Lexer {
        return myLexer
    }
    
    override fun getTokenHighlights(tokenType: IElementType?): Array<TextAttributesKey> {
        val result = elementTypeMap[tokenType]
        if (result != null) return result
        
        if (tokenType !is RobotTextMateElementType) return PLAIN_SYNTAX_HIGHLIGHTER.getTokenHighlights(tokenType)
        
        val service = TextMateService.getInstance()
        val customHighlightingColors = service.customHighlightingColors
        
        val highlightingRules = ContainerUtil.union(customHighlightingColors.keys, TextMateTheme.INSTANCE.rules)
        
        val textMateScope = trimEmbeddedScope(tokenType)
        val selectors: List<CharSequence> = ContainerUtil.reverse(
            TextMateScopeComparator(textMateScope, Function.identity())
                .sortAndFilter(highlightingRules)
        )
        val result1 = ContainerUtil.map2Array(
            selectors,
            TextAttributesKey::class.java
        ) { rule: CharSequence ->
            val customTextAttributes = customHighlightingColors[rule]
            customTextAttributes?.getTextAttributesKey(TextMateTheme.INSTANCE)
                ?: TextMateTheme.INSTANCE.getTextAttributesKey(rule)
        }
        
        return result1
    }
    
    private fun trimEmbeddedScope(tokenType: RobotTextMateElementType): TextMateScope {
        var current: TextMateScope? = tokenType.scope
        val trail: MutableList<CharSequence?> = ArrayList()
        while (current != null) {
            val scopeName = current.scopeName
            if (scopeName != null && scopeName.contains(".embedded.")) {
                var result = TextMateScope.EMPTY
                for (i in trail.indices.reversed()) {
                    result = result.add(trail[i])
                }
                return result
            }
            trail.add(scopeName)
            current = current.parent
        }
        return tokenType.scope
    }
}

