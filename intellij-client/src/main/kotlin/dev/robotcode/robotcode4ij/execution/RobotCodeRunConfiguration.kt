package dev.robotcode.robotcode4ij.execution

import com.intellij.execution.Executor
import com.intellij.execution.configurations.ConfigurationFactory
import com.intellij.execution.configurations.LocatableConfigurationBase
import com.intellij.execution.configurations.RunConfiguration
import com.intellij.execution.configurations.RunProfileState
import com.intellij.execution.runners.ExecutionEnvironment
import com.intellij.execution.testframework.sm.runner.SMRunnerConsolePropertiesProvider
import com.intellij.execution.testframework.sm.runner.SMTRunnerConsoleProperties
import com.intellij.openapi.options.SettingsEditor
import com.intellij.openapi.project.Project
import dev.robotcode.robotcode4ij.testing.RobotCodeTestItem
import org.jdom.Element
import com.intellij.util.xmlb.XmlSerializer

class RobotCodeRunConfiguration(project: Project, factory: ConfigurationFactory) :
    LocatableConfigurationBase<ConfigurationFactory>
        (project, factory, "Robot Framework"), SMRunnerConsolePropertiesProvider {
    
    override fun getState(executor: Executor, environment: ExecutionEnvironment): RunProfileState {
        return RobotCodeRunProfileState(this, environment)
    }
    
    override fun getConfigurationEditor(): SettingsEditor<out RunConfiguration> {
        return RobotCodeRunConfigurationEditor()
    }
    
    var includedTestItems: List<RobotCodeTestItem> = emptyList()
    
    var paths: List<String> = emptyList()
    
    var isAttachDebugger: Boolean = false // Add this property for the checkbox
    
    override fun createTestConsoleProperties(executor: Executor): SMTRunnerConsoleProperties {
        return RobotRunnerConsoleProperties(this, "Robot Framework", executor)
    }
    
    override fun writeExternal(element: Element) {
        super.writeExternal(element)
        XmlSerializer.serializeInto(this, element)
    }
    
    override fun readExternal(element: Element) {
        super.readExternal(element)
        XmlSerializer.deserializeInto(this, element)
    }
}
